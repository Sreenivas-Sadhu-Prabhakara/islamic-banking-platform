package com.bank.platform.controlrecord.store;

import com.bank.platform.controlrecord.spec.BehaviourQualifierSpec;
import com.bank.platform.controlrecord.spec.ControlRecordSpec;
import com.bank.platform.controlrecord.spec.Field;
import org.springframework.jdbc.core.JdbcTemplate;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

/**
 * The one JDBC repository in the estate. It replaces a 247-line generated
 * repository per service domain — 53 of them from the catalog, and a
 * {@code ConcurrentHashMap} in the 203 already on disk.
 */
public class JdbcControlRecordStore implements ControlRecordStore {

    private final JdbcTemplate jdbc;
    private final ControlRecordSpec spec;

    public JdbcControlRecordStore(JdbcTemplate jdbc, ControlRecordSpec spec) {
        this.jdbc = jdbc;
        this.spec = spec;
    }

    @Override
    public Map<String, Object> insert(String tenantId, Map<String, Object> record) {
        List<Object> args = new ArrayList<>();
        args.add(tenantId);
        for (Field f : spec.fields()) {
            args.addAll(ValueCodec.toColumns(f, record.get(f.name())));
        }
        jdbc.update(ControlRecordSql.insert(spec), args.toArray());
        String id = String.valueOf(record.get(spec.primaryKey()));
        return findById(tenantId, id).orElseThrow(() -> new IllegalStateException(
                "inserted " + spec.name() + " " + id + " is not readable back"));
    }

    @Override
    public Optional<Map<String, Object>> findById(String tenantId, String id) {
        List<Map<String, Object>> rows =
                jdbc.queryForList(ControlRecordSql.selectById(spec), tenantId, id);
        return rows.isEmpty() ? Optional.empty() : Optional.of(toWire(rows.get(0)));
    }

    @Override
    public List<Map<String, Object>> findAll(String tenantId, int limit) {
        return jdbc.queryForList(ControlRecordSql.selectAll(spec), tenantId, limit)
                .stream().map(this::toWire).toList();
    }

    @Override
    public Optional<Map<String, Object>> update(String tenantId, String id, Map<String, Object> patch) {
        List<String> columns = new ArrayList<>();
        List<Object> args = new ArrayList<>();
        for (Field f : spec.fields()) {
            if (!patch.containsKey(f.name()) || f.name().equals(spec.primaryKey())) {
                continue;
            }
            f.columns().forEach(c -> columns.add(c.name()));
            args.addAll(ValueCodec.toColumns(f, patch.get(f.name())));
        }
        if (columns.isEmpty()) {
            return findById(tenantId, id);
        }
        args.add(tenantId);
        args.add(id);
        int changed = jdbc.update(ControlRecordSql.update(spec, columns), args.toArray());
        return changed == 0 ? Optional.empty() : findById(tenantId, id);
    }

    @Override
    public List<Map<String, Object>> findBehaviourQualifier(String tenantId, String recordId,
                                                            BehaviourQualifierSpec qualifier) {
        String sql = ControlRecordSql.selectBehaviourQualifier(qualifier, spec);
        return jdbc.queryForList(sql, tenantId, recordId).stream()
                .map(row -> toWire(row, qualifier.fields())).toList();
    }

    private Map<String, Object> toWire(Map<String, Object> row) {
        return toWire(row, spec.fields());
    }

    private Map<String, Object> toWire(Map<String, Object> row, List<Field> fields) {
        Map<String, Object> normalised = new LinkedHashMap<>();
        row.forEach((k, v) -> normalised.put(k.toLowerCase(), v));
        Map<String, Object> out = new LinkedHashMap<>();
        for (Field f : fields) {
            Object value = ValueCodec.fromColumns(f, normalised);
            if (value != null) {
                out.put(f.name(), value);
            }
        }
        return out;
    }
}
