package com.bank.platform.controlrecord.api;

import com.bank.platform.controlrecord.spec.BehaviourQualifierSpec;
import com.bank.platform.controlrecord.spec.DomainSpec;
import org.springframework.web.servlet.function.RouterFunction;
import org.springframework.web.servlet.function.RouterFunctions;
import org.springframework.web.servlet.function.ServerRequest;
import org.springframework.web.servlet.function.ServerResponse;

import java.util.LinkedHashMap;
import java.util.Map;

/**
 * The only Spring-coupled class in the engine: it maps the catalog's paths
 * onto {@link ControlRecordHandler}'s methods.
 *
 * Functional routes rather than {@code @RestController} because the paths are
 * DATA — {@code /v1/<control-record-slug>/…} differs per domain, and an
 * annotation cannot be computed. This is what lets one jar serve any domain in
 * the catalog instead of 53 generated controllers.
 */
public final class ControlRecordRoutes {

    private ControlRecordRoutes() { }

    public static RouterFunction<ServerResponse> of(DomainSpec domain,
                                                    ControlRecordHandler handler,
                                                    TenantResolver tenants) {
        String base = "/v1/" + domain.controlRecordSlug();
        RouterFunctions.Builder routes = RouterFunctions.route()
                .GET("/v1/service-domain", request -> respond(handler.serviceDomain()))
                .POST(base + "/initiate", request ->
                        respond(handler.initiate(tenants.resolve(request), body(request))))
                .GET(base + "/{crId}/retrieve", request ->
                        respond(handler.retrieve(tenants.resolve(request), request.pathVariable("crId"))))
                .PUT(base + "/{crId}/update", request ->
                        respond(handler.update(tenants.resolve(request),
                                request.pathVariable("crId"), body(request))))
                .PUT(base + "/{crId}/control", request ->
                        respond(handler.control(tenants.resolve(request),
                                request.pathVariable("crId"), body(request))))
                .GET(base, request -> respond(handler.retrieveAll(tenants.resolve(request),
                        request.param("limit").map(Integer::valueOf).orElse(null))));

        for (BehaviourQualifierSpec qualifier : domain.behaviourQualifiers()) {
            routes = routes.GET(base + "/{crId}/" + qualifier.path(), request ->
                    respond(handler.retrieveQualifier(tenants.resolve(request),
                            request.pathVariable("crId"), qualifier.path())));
        }

        return routes
                // A request with no resolvable tenant is refused, never served
                // against a default tenant's rows.
                .onError(IllegalStateException.class, (error, request) ->
                        respond(new ControlRecordHandler.Response(400,
                                problem("NO_TENANT", error.getMessage()))))
                .onError(IllegalArgumentException.class, (error, request) ->
                        respond(new ControlRecordHandler.Response(400,
                                problem("MALFORMED", error.getMessage()))))
                .build();
    }

    @SuppressWarnings("unchecked")
    private static Map<String, Object> body(ServerRequest request) throws Exception {
        Map<String, Object> parsed = request.body(Map.class);
        return parsed == null ? Map.of() : parsed;
    }

    private static ServerResponse respond(ControlRecordHandler.Response response) {
        return ServerResponse.status(response.status()).body(response.body());
    }

    private static Map<String, Object> problem(String code, String message) {
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("error", code);
        out.put("message", message);
        return out;
    }
}
