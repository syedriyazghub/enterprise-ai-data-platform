using AuthService.Data;
using AuthService.Services;
using AuthService.Middleware;
using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.EntityFrameworkCore;
using Microsoft.IdentityModel.Tokens;
using Microsoft.OpenApi.Models;
using OpenTelemetry.Resources;
using OpenTelemetry.Trace;
using Serilog;
using System.Text;

var builder = WebApplication.CreateBuilder(args);

// ─── Serilog ──────────────────────────────────────────────────────────────────
Log.Logger = new LoggerConfiguration()
    .WriteTo.Console(outputTemplate: "[{Timestamp:HH:mm:ss} {Level:u3}] {Message:lj}{NewLine}{Exception}")
    .Enrich.FromLogContext()
    .CreateLogger();
builder.Host.UseSerilog();

// ─── Database ─────────────────────────────────────────────────────────────────
builder.Services.AddDbContext<AuthDbContext>(opts =>
    opts.UseNpgsql(builder.Configuration.GetConnectionString("DefaultConnection")));

// ─── JWT Authentication ───────────────────────────────────────────────────────
var jwtSecret = builder.Configuration["Jwt:Secret"]
    ?? throw new InvalidOperationException("Jwt:Secret must be configured");
var key = Encoding.UTF8.GetBytes(jwtSecret);

builder.Services.AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
    .AddJwtBearer(opts =>
    {
        opts.TokenValidationParameters = new TokenValidationParameters
        {
            ValidateIssuerSigningKey = true,
            IssuerSigningKey         = new SymmetricSecurityKey(key),
            ValidateIssuer           = true,
            ValidIssuer              = builder.Configuration["Jwt:Issuer"],
            ValidateAudience         = true,
            ValidAudience            = builder.Configuration["Jwt:Audience"],
            ValidateLifetime         = true,
            ClockSkew                = TimeSpan.Zero,
        };
    });

builder.Services.AddAuthorization();

// ─── Services ─────────────────────────────────────────────────────────────────
builder.Services.AddScoped<ITokenService, TokenService>();
builder.Services.AddScoped<IAuthService, AuthenticationService>();

// ─── OpenTelemetry ────────────────────────────────────────────────────────────
builder.Services.AddOpenTelemetry()
    .WithTracing(tracing => tracing
        .SetResourceBuilder(ResourceBuilder.CreateDefault().AddService("auth-service"))
        .AddAspNetCoreInstrumentation()
        .AddEntityFrameworkCoreInstrumentation()
        .AddOtlpExporter(opts =>
            opts.Endpoint = new Uri(builder.Configuration["Otel:Endpoint"] ?? "http://localhost:4317")));

// ─── Swagger ──────────────────────────────────────────────────────────────────
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen(c =>
{
    c.SwaggerDoc("v1", new OpenApiInfo { Title = "Auth Service", Version = "v1",
        Description = "JWT authentication, registration, token refresh and revocation" });
    c.AddSecurityDefinition("Bearer", new OpenApiSecurityScheme
    {
        Type = SecuritySchemeType.Http, Scheme = "bearer", BearerFormat = "JWT",
        Description = "Enter your JWT token",
    });
    c.AddSecurityRequirement(new OpenApiSecurityRequirement
    {
        {
            new OpenApiSecurityScheme
            {
                Reference = new OpenApiReference { Type = ReferenceType.SecurityScheme, Id = "Bearer" }
            },
            Array.Empty<string>()
        }
    });
});

// ─── CORS — restrict to configured origins ────────────────────────────────────
var allowedOrigins = builder.Configuration.GetSection("AllowedOrigins").Get<string[]>()
    ?? new[] { "http://localhost:3000", "http://localhost:8000" };

builder.Services.AddCors(opts => opts.AddDefaultPolicy(p =>
    p.WithOrigins(allowedOrigins)
     .AllowAnyMethod()
     .AllowAnyHeader()
     .AllowCredentials()));

// ─── Health Checks ────────────────────────────────────────────────────────────
builder.Services.AddHealthChecks()
    .AddNpgSql(builder.Configuration.GetConnectionString("DefaultConnection")!);

var app = builder.Build();

app.UseSerilogRequestLogging();
app.UseSwagger();
app.UseSwaggerUI();
app.UseCors();
app.UseAuthentication();
app.UseAuthorization();
app.UseMiddleware<RequestIdMiddleware>();

// ─── Health ───────────────────────────────────────────────────────────────────
app.MapGet("/health", () => Results.Ok(new { status = "healthy", service = "auth-service" }))
   .WithTags("Health").ExcludeFromDescription();

app.MapHealthChecks("/health/ready");

// ─── Auth Endpoints ───────────────────────────────────────────────────────────
app.MapPost("/api/v1/auth/register", async (RegisterRequest req, IAuthService authSvc) =>
{
    var result = await authSvc.RegisterAsync(req);
    return result.Success
        ? Results.Created("/api/v1/auth/me", result)
        : Results.BadRequest(new { result.Message });
}).WithTags("Auth").WithSummary("Register a new user");

app.MapPost("/api/v1/auth/login", async (LoginRequest req, IAuthService authSvc) =>
{
    var result = await authSvc.LoginAsync(req);
    return result.Success ? Results.Ok(result) : Results.Unauthorized();
}).WithTags("Auth").WithSummary("Login and get JWT token");

app.MapPost("/api/v1/auth/refresh", async (RefreshRequest req, IAuthService authSvc) =>
{
    var result = await authSvc.RefreshTokenAsync(req.RefreshToken);
    return result.Success ? Results.Ok(result) : Results.Unauthorized();
}).WithTags("Auth").WithSummary("Refresh JWT token");

app.MapPost("/api/v1/auth/logout", async (RefreshRequest req, IAuthService authSvc) =>
{
    await authSvc.RevokeTokenAsync(req.RefreshToken);
    return Results.Ok(new { message = "Logged out successfully" });
}).WithTags("Auth").WithSummary("Revoke refresh token (logout)");

app.MapGet("/api/v1/auth/me", (HttpContext ctx) =>
{
    var userId   = ctx.User.FindFirst("sub")?.Value;
    var email    = ctx.User.FindFirst("email")?.Value;
    var role     = ctx.User.FindFirst("role")?.Value;
    var tenantId = ctx.User.FindFirst("tenant_id")?.Value;
    return Results.Ok(new { userId, email, role, tenantId });
}).RequireAuthorization().WithTags("Auth").WithSummary("Get current user info");

app.MapGet("/api/v1/auth/validate", (HttpContext ctx) =>
{
    // Used by gateway to validate tokens
    var userId = ctx.User.FindFirst("sub")?.Value;
    return userId != null
        ? Results.Ok(new { valid = true, userId, tenantId = ctx.User.FindFirst("tenant_id")?.Value })
        : Results.Unauthorized();
}).RequireAuthorization().WithTags("Auth").WithSummary("Validate JWT token (used by gateway)");

// ─── Apply Migrations ─────────────────────────────────────────────────────────
using (var scope = app.Services.CreateScope())
{
    var db = scope.ServiceProvider.GetRequiredService<AuthDbContext>();
    await db.Database.MigrateAsync();
}

app.Run();
