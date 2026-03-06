using System;

/// <summary>
/// Static API wrapper for economy endpoints.
/// Uses ApiClient.Instance for all HTTP requests.
/// </summary>
public static class EconomyApi
{
    /// <summary>
    /// Fetches the player's current gold and gems balance.
    /// Requires authentication.
    /// </summary>
    public static void GetBalance(
        Action<BalanceResponse> onSuccess, Action<string> onError)
    {
        ApiClient.Instance.StartRequest(
            ApiClient.Instance.Get<BalanceResponse>(
                "/economy/balance", onSuccess, onError)
        );
    }
}
