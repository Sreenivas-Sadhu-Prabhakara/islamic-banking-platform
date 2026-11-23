package com.bank.platform.controlrecord.api;

import com.bank.platform.controlrecord.spec.BehaviourQualifierSpec;
import com.bank.platform.controlrecord.spec.DomainSpec;
import com.bank.platform.controlrecord.spec.Field;
import com.bank.platform.controlrecord.store.ControlRecordStore;
import com.bank.platform.controlrecord.validate.RecordValidator;
import com.bank.platform.controlrecord.validate.Violation;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

/**
 * The BIAN action terms, as plain methods.
 *
 * Nothing here imports a web framework: every method takes values and returns
 * a {@link Response}, so the whole API surface is unit-testable without
 * starting a servlet container. {@link ControlRecordRoutes} is the only
 * Spring-coupled class, and it is a thin adapter.
 *
 * This replaces a 161-line generated controller per service domain, and the
 * 85-line {@code ServiceDomainController} copied into 203 repos.
 */
public class ControlRecordHandler {

    /** The three BIAN Control actions, and the status each one moves the record to. */
    private static final Map<String, String> CONTROL_ACTIONS =
            Map.of("suspend", "SUSPENDED", "resume", "ACTIVE", "terminate", "TERMINATED");

    private final DomainSpec domain;
    private final ControlRecordStore store;
    private final RecordValidator validator;
    private final int defaultLimit;

    public ControlRecordHandler(DomainSpec domain, ControlRecordStore store, int defaultLimit) {
        this.domain = domain;
        this.store = store;
        this.validator = new RecordValidator(domain.controlRecord());
        this.defaultLimit = defaultLimit;
    }

    public record Response(int status, Object body) { }

    /** GET /v1/service-domain — what this service domain is, from the catalog. */
    public Response serviceDomain() {
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("serviceDomain", domain.name());
        out.put("businessArea", domain.businessArea());
        out.put("businessDomain", domain.businessDomain());
        out.put("functionalPattern", domain.functionalPattern());
        out.put("assetType", domain.assetType());
        out.put("controlRecord", domain.controlRecordName());
        out.put("fields", domain.controlRecord().fields().size());
        out.put("behaviourQualifiers", domain.behaviourQualifiers().stream()
                .map(BehaviourQualifierSpec::path).toList());
        out.put("controlActions", availableActions());
        out.put("servedBy", "control-record-engine");
        return new Response(200, out);
    }

    /** POST /v1/{cr}/initiate */
    public Response initiate(String tenantId, Map<String, Object> body) {
        List<Violation> violations = validator.validate(body, false);
        if (!violations.isEmpty()) {
            return unprocessable(violations);
        }
        Object id = body.get(domain.controlRecord().primaryKey());
        if (id == null) {
            return new Response(400, error("MISSING_ID",
                    domain.controlRecord().primaryKey() + " is the primary key and must be supplied"));
        }
        return new Response(201, store.insert(tenantId, body));
    }

    /** GET /v1/{cr} */
    public Response retrieveAll(String tenantId, Integer limit) {
        int effective = limit == null || limit <= 0 ? defaultLimit : Math.min(limit, defaultLimit);
        return new Response(200, store.findAll(tenantId, effective));
    }

    /** GET /v1/{cr}/{crId}/retrieve */
    public Response retrieve(String tenantId, String recordId) {
        return store.findById(tenantId, recordId)
                .map(r -> new Response(200, r))
                .orElseGet(this::notFound);
    }

    /** PUT /v1/{cr}/{crId}/update */
    public Response update(String tenantId, String recordId, Map<String, Object> body) {
        List<Violation> violations = validator.validate(body, true);
        if (!violations.isEmpty()) {
            return unprocessable(violations);
        }
        if (body.containsKey(domain.controlRecord().primaryKey())) {
            return new Response(400, error("IMMUTABLE_ID", "the primary key cannot be updated"));
        }
        return store.update(tenantId, recordId, body)
                .map(r -> new Response(200, r))
                .orElseGet(this::notFound);
    }

    /**
     * PUT /v1/{cr}/{crId}/control — suspend | resume | terminate.
     *
     * The offered actions come from the domain's own status enum. A domain
     * whose catalog entry declares no SUSPENDED value does not get a suspend
     * action, where the scaffold hardcoded all four statuses for every domain
     * whether its lifecycle had them or not.
     */
    public Response control(String tenantId, String recordId, Map<String, Object> body) {
        Optional<Field> status = domain.controlRecord().statusField();
        if (status.isEmpty()) {
            return new Response(400, error("NO_LIFECYCLE",
                    domain.name() + " declares no status field, so it has no control actions"));
        }
        Object requested = body == null ? null : body.get("action");
        String action = requested == null ? "" : String.valueOf(requested).toLowerCase();
        String target = CONTROL_ACTIONS.get(action);
        if (target == null || !availableActions().contains(action)) {
            return new Response(400, error("UNKNOWN_ACTION",
                    "'" + requested + "' is not an action of this domain — use "
                            + availableActions()));
        }
        return store.update(tenantId, recordId, Map.of(status.get().name(), target))
                .map(r -> new Response(200, r))
                .orElseGet(this::notFound);
    }

    /** GET /v1/{cr}/{crId}/{bqPath} */
    public Response retrieveQualifier(String tenantId, String recordId, String path) {
        Optional<BehaviourQualifierSpec> qualifier = domain.behaviourQualifier(path);
        if (qualifier.isEmpty()) {
            return notFound();
        }
        if (store.findById(tenantId, recordId).isEmpty()) {
            return notFound();
        }
        return new Response(200, store.findBehaviourQualifier(tenantId, recordId, qualifier.get()));
    }

    /** The subset of BIAN control actions this domain's status enum can actually reach. */
    public List<String> availableActions() {
        return domain.controlRecord().statusField()
                .map(f -> CONTROL_ACTIONS.entrySet().stream()
                        .filter(e -> f.permitted().contains(e.getValue()))
                        .map(Map.Entry::getKey).sorted().toList())
                .orElse(List.of());
    }

    private Response notFound() {
        return new Response(404, error("NOT_FOUND", "unknown control record id"));
    }

    private Response unprocessable(List<Violation> violations) {
        Map<String, Object> body = new LinkedHashMap<>();
        body.put("error", "VALIDATION_FAILED");
        body.put("controlRecord", domain.controlRecordName());
        body.put("violations", violations);
        return new Response(422, body);
    }

    private static Map<String, Object> error(String code, String message) {
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("error", code);
        out.put("message", message);
        return out;
    }
}
