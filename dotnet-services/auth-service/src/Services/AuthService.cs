namespace AuthService.Services;

// ─── Request/Response Models ──────────────────────────────────────────────────

public record RegisterRequest(
    string Email,
    string Password,
    string FirstName,
    string LastName,
    string TenantId = "default",
    string Role = "user");

public record LoginRequest(string Email, string Password);
public record RefreshRequest(string RefreshToken);

public record AuthResult(
    bool Success,
    string? Token = null,
    string? RefreshToken = null,
    string? UserId = null,
    string? Role = null,
    string? TenantId = null,
    string? Message = null);

// ─── Token Service ────────────────────────────────────────────────────────────

public interface ITokenService
{
    string GenerateAccessToken(AuthService.Data.User user);
    string GenerateRefreshToken();
}

/// <summary>
/// Generates JWT tokens using System.IdentityModel.Tokens.Jwt so they
/// validate correctly against the JwtBearer middleware configured in Program.cs.
/// </summary>
public class TokenService(IConfiguration config) : ITokenService
{
    public string GenerateAccessToken(AuthService.Data.User user)
    {
        var secret = config["Jwt:Secret"] ?? throw new InvalidOperationException("Jwt:Secret not configured");
        var key = new Microsoft.IdentityModel.Tokens.SymmetricSecurityKey(
            System.Text.Encoding.UTF8.GetBytes(secret));
        var creds = new Microsoft.IdentityModel.Tokens.SigningCredentials(
            key, Microsoft.IdentityModel.Tokens.SecurityAlgorithms.HmacSha256);

        var expiryMinutes = int.Parse(config["Jwt:ExpiryMinutes"] ?? "60");

        var claims = new[]
        {
            new System.Security.Claims.Claim("sub",       user.Id.ToString()),
            new System.Security.Claims.Claim("email",     user.Email),
            new System.Security.Claims.Claim("role",      user.Role),
            new System.Security.Claims.Claim("tenant_id", user.TenantId),
            new System.Security.Claims.Claim("given_name",user.FirstName),
            new System.Security.Claims.Claim("family_name",user.LastName),
        };

        var token = new System.IdentityModel.Tokens.Jwt.JwtSecurityToken(
            issuer:             config["Jwt:Issuer"],
            audience:           config["Jwt:Audience"],
            claims:             claims,
            notBefore:          DateTime.UtcNow,
            expires:            DateTime.UtcNow.AddMinutes(expiryMinutes),
            signingCredentials: creds);

        return new System.IdentityModel.Tokens.Jwt.JwtSecurityTokenHandler().WriteToken(token);
    }

    public string GenerateRefreshToken()
    {
        var bytes = new byte[64];
        System.Security.Cryptography.RandomNumberGenerator.Fill(bytes);
        return Convert.ToBase64String(bytes);
    }
}

// ─── Auth Service ─────────────────────────────────────────────────────────────

public interface IAuthService
{
    Task<AuthResult> RegisterAsync(RegisterRequest request);
    Task<AuthResult> LoginAsync(LoginRequest request);
    Task<AuthResult> RefreshTokenAsync(string refreshToken);
    Task<bool> RevokeTokenAsync(string refreshToken);
}

public class AuthenticationService(
    AuthService.Data.AuthDbContext db,
    ITokenService tokenService,
    IConfiguration config) : IAuthService
{
    public async Task<AuthResult> RegisterAsync(RegisterRequest request)
    {
        if (await db.Users.AnyAsync(u => u.Email == request.Email.ToLower()))
            return new AuthResult(false, Message: "Email already registered");

        if (request.Password.Length < 8)
            return new AuthResult(false, Message: "Password must be at least 8 characters");

        var user = new AuthService.Data.User
        {
            Email       = request.Email.ToLower(),
            PasswordHash = BCrypt.Net.BCrypt.HashPassword(request.Password, workFactor: 12),
            FirstName   = request.FirstName,
            LastName    = request.LastName,
            TenantId    = request.TenantId,
            Role        = request.Role,
        };

        db.Users.Add(user);
        await db.SaveChangesAsync();

        var token   = tokenService.GenerateAccessToken(user);
        var refresh = await CreateRefreshTokenAsync(user);

        return new AuthResult(true,
            Token: token, RefreshToken: refresh,
            UserId: user.Id.ToString(), Role: user.Role, TenantId: user.TenantId);
    }

    public async Task<AuthResult> LoginAsync(LoginRequest request)
    {
        var user = await db.Users.FirstOrDefaultAsync(u => u.Email == request.Email.ToLower());
        if (user == null || !BCrypt.Net.BCrypt.Verify(request.Password, user.PasswordHash))
            return new AuthResult(false, Message: "Invalid credentials");

        if (!user.IsActive)
            return new AuthResult(false, Message: "Account is disabled");

        user.LastLoginAt = DateTime.UtcNow;
        await db.SaveChangesAsync();

        var token   = tokenService.GenerateAccessToken(user);
        var refresh = await CreateRefreshTokenAsync(user);

        return new AuthResult(true,
            Token: token, RefreshToken: refresh,
            UserId: user.Id.ToString(), Role: user.Role, TenantId: user.TenantId);
    }

    public async Task<AuthResult> RefreshTokenAsync(string refreshToken)
    {
        var token = await db.RefreshTokens
            .Include(t => t.User)
            .FirstOrDefaultAsync(t =>
                t.Token == refreshToken &&
                !t.IsRevoked &&
                t.ExpiresAt > DateTime.UtcNow);

        if (token == null)
            return new AuthResult(false, Message: "Invalid or expired refresh token");

        // Rotate: revoke old, issue new
        token.IsRevoked = true;
        var newAccess  = tokenService.GenerateAccessToken(token.User);
        var newRefresh = await CreateRefreshTokenAsync(token.User);
        await db.SaveChangesAsync();

        return new AuthResult(true, Token: newAccess, RefreshToken: newRefresh,
            UserId: token.User.Id.ToString(), Role: token.User.Role, TenantId: token.User.TenantId);
    }

    public async Task<bool> RevokeTokenAsync(string refreshToken)
    {
        var token = await db.RefreshTokens.FirstOrDefaultAsync(t => t.Token == refreshToken);
        if (token == null) return false;
        token.IsRevoked = true;
        await db.SaveChangesAsync();
        return true;
    }

    private async Task<string> CreateRefreshTokenAsync(AuthService.Data.User user)
    {
        var expiryDays = int.Parse(config["Jwt:RefreshExpiryDays"] ?? "7");
        var refreshToken = new AuthService.Data.RefreshToken
        {
            UserId    = user.Id,
            Token     = tokenService.GenerateRefreshToken(),
            ExpiresAt = DateTime.UtcNow.AddDays(expiryDays),
        };
        db.RefreshTokens.Add(refreshToken);
        await db.SaveChangesAsync();
        return refreshToken.Token;
    }
}
