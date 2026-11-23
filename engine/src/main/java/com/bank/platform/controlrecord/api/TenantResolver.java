package com.bank.platform.controlrecord.api;

import org.springframework.web.servlet.function.ServerRequest;

/**
 * Resolves the tenant for a request, and fails closed.
 *
 * There is no default tenant and no fallback: a request whose tenant cannot be
 * resolved is rejected rather than served against someone's data. In
 * production this reads a verified token claim; the header form exists so a
 * service can be driven in a test or a demo without an authorization server.
 */
public interface TenantResolver {

    String resolve(ServerRequest request);

    /** Reads the tenant from a request header, rejecting a request without one. */
    static TenantResolver header(String headerName) {
        return request -> request.headers().firstHeader(headerName) != null
                ? request.headers().firstHeader(headerName)
                : fail(headerName);
    }

    private static String fail(String headerName) {
        throw new IllegalStateException(
                "no tenant on the request: " + headerName + " is absent and there is no default tenant");
    }
}
