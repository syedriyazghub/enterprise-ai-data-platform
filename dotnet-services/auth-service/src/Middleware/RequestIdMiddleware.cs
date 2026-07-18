namespace AuthService.Middleware;

/// <summary>Attaches a unique X-Request-ID header to every request.</summary>
public class RequestIdMiddleware(RequestDelegate next)
{
    public async Task InvokeAsync(HttpContext context)
    {
        var requestId = context.Request.Headers["X-Request-ID"].FirstOrDefault()
            ?? Guid.NewGuid().ToString();
        context.Response.Headers["X-Request-ID"] = requestId;
        await next(context);
    }
}
