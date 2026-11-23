package com.bank.platform.controlrecord.store;

import com.bank.platform.controlrecord.spec.BehaviourQualifierSpec;

import java.util.List;
import java.util.Map;
import java.util.Optional;

/**
 * Persistence for one service domain's control record.
 *
 * Every method takes the tenant explicitly. There is deliberately no
 * tenant-free overload and no ambient "current tenant" — a caller that has not
 * resolved the tenant cannot read a row.
 *
 * There is also deliberately no in-memory implementation. The scaffold's
 * {@code ConcurrentHashMap} is what let 203 services "deploy and answer real
 * requests" while storing nothing, and an in-memory fallback in a banking
 * service is a data-loss bug that passes its own tests.
 */
public interface ControlRecordStore {

    Map<String, Object> insert(String tenantId, Map<String, Object> record);

    Optional<Map<String, Object>> findById(String tenantId, String id);

    List<Map<String, Object>> findAll(String tenantId, int limit);

    Optional<Map<String, Object>> update(String tenantId, String id, Map<String, Object> patch);

    List<Map<String, Object>> findBehaviourQualifier(String tenantId, String recordId,
                                                     BehaviourQualifierSpec qualifier);
}
