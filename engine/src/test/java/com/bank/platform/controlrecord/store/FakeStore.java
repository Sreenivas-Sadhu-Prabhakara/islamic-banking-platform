package com.bank.platform.controlrecord.store;

import com.bank.platform.controlrecord.spec.BehaviourQualifierSpec;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

/**
 * A store for the handler tests only.
 *
 * It lives in src/test on purpose: an in-memory implementation on the main
 * source path is how the scaffold's ConcurrentHashMap ended up serving
 * production traffic in 203 services.
 */
public class FakeStore implements ControlRecordStore {

    private final Map<String, Map<String, Map<String, Object>>> byTenant = new LinkedHashMap<>();
    public final List<Map<String, Object>> qualifierRows = new ArrayList<>();

    @Override
    public Map<String, Object> insert(String tenantId, Map<String, Object> record) {
        String id = String.valueOf(record.values().iterator().next());
        byTenant.computeIfAbsent(tenantId, t -> new LinkedHashMap<>())
                .put(id, new LinkedHashMap<>(record));
        return new LinkedHashMap<>(record);
    }

    @Override
    public Optional<Map<String, Object>> findById(String tenantId, String id) {
        return Optional.ofNullable(byTenant.getOrDefault(tenantId, Map.of()).get(id));
    }

    @Override
    public List<Map<String, Object>> findAll(String tenantId, int limit) {
        return byTenant.getOrDefault(tenantId, Map.of()).values().stream().limit(limit).toList();
    }

    @Override
    public Optional<Map<String, Object>> update(String tenantId, String id, Map<String, Object> patch) {
        return findById(tenantId, id).map(existing -> {
            existing.putAll(patch);
            return existing;
        });
    }

    @Override
    public List<Map<String, Object>> findBehaviourQualifier(String tenantId, String recordId,
                                                            BehaviourQualifierSpec qualifier) {
        return qualifierRows;
    }

    public void seed(String tenantId, String id, Map<String, Object> record) {
        byTenant.computeIfAbsent(tenantId, t -> new LinkedHashMap<>())
                .put(id, new LinkedHashMap<>(record));
    }
}
