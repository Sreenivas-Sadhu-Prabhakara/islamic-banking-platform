package com.bank.platform.controlrecord.spec;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.io.IOException;
import java.io.InputStream;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Reads catalog schema v2 into {@link DomainSpec}s.
 *
 * The catalog is the only per-domain input in the estate: 53 domains, 2,813
 * fields, 254 behaviour qualifiers. Reading it at runtime is what lets one
 * engine serve all of them.
 *
 * This reader is strict in the one way that matters: an unknown field type
 * throws rather than degrading to a free-form string column, and every table
 * and column name passes {@link Identifiers} before it can reach a statement.
 */
public final class CatalogReader {

    private static final ObjectMapper MAPPER = new ObjectMapper();

    private CatalogReader() { }

    /** Every service domain in the catalog, keyed by repo slug ({@code isb-<slug>} without the prefix). */
    public static Map<String, DomainSpec> readAll(InputStream catalog) throws IOException {
        JsonNode root = MAPPER.readTree(catalog);
        Map<String, DomainSpec> out = new LinkedHashMap<>();
        for (JsonNode area : root.path("businessAreas")) {
            for (JsonNode domain : area.path("businessDomains")) {
                for (JsonNode sd : domain.path("serviceDomains")) {
                    DomainSpec spec = domainSpec(sd, area.path("name").asText(),
                            domain.path("name").asText());
                    out.put(spec.slug(), spec);
                }
            }
        }
        return Map.copyOf(out);
    }

    public static DomainSpec read(InputStream catalog, String slug) throws IOException {
        DomainSpec spec = readAll(catalog).get(slug);
        if (spec == null) {
            throw new IllegalArgumentException("no service domain '" + slug + "' in the catalog");
        }
        return spec;
    }

    private static DomainSpec domainSpec(JsonNode sd, String area, String businessDomain) {
        JsonNode cr = sd.get("controlRecord");
        if (cr == null) {
            throw new IllegalArgumentException(
                    "service domain '" + sd.path("name").asText() + "' has no controlRecord: "
                            + "this is a catalog v1 entry, and v1 is what produced the identical scaffolds");
        }
        ControlRecordSpec record = new ControlRecordSpec(
                cr.path("name").asText(),
                cr.path("table").asText(),
                cr.path("primaryKey").asText(),
                fields(cr.path("fields")));

        List<BehaviourQualifierSpec> bqs = new ArrayList<>();
        for (JsonNode bq : sd.path("behaviourQualifiers")) {
            // A qualifier with no fields gets no table and no path, by design.
            if (bq.path("noSchema").asBoolean(false) || !bq.path("fields").isArray()
                    || bq.path("fields").isEmpty()) {
                continue;
            }
            bqs.add(new BehaviourQualifierSpec(
                    bq.path("name").asText(),
                    bq.path("path").asText(),
                    bq.path("table").asText(),
                    fields(bq.path("fields"))));
        }

        String name = sd.path("name").asText();
        return new DomainSpec(name, DomainSpec.slugify(name),
                sd.path("functionalPattern").asText(), sd.path("assetType").asText(),
                area, businessDomain, record.name(), record, bqs);
    }

    private static List<Field> fields(JsonNode array) {
        List<Field> out = new ArrayList<>();
        for (JsonNode f : array) {
            String name = f.path("name").asText();
            String column = f.hasNonNull("column") ? f.get("column").asText() : snake(name);
            Identifiers.require(column, "field.column of '" + name + "'");
            List<String> values = new ArrayList<>();
            for (JsonNode v : f.path("values")) {
                values.add(v.asText());
            }
            out.add(new Field(
                    name,
                    column,
                    FieldType.of(f.path("type").asText()),
                    f.path("required").asBoolean(false),
                    values,
                    f.hasNonNull("const") ? literal(f.get("const")) : null,
                    f.hasNonNull("currencyField") ? f.get("currencyField").asText() : null,
                    f.path("nonNegative").asBoolean(false),
                    f.hasNonNull("maxDenominator") ? f.get("maxDenominator").asLong() : null,
                    f.hasNonNull("min") ? f.get("min").asInt() : null,
                    f.hasNonNull("max") ? f.get("max").asInt() : null,
                    f.hasNonNull("maxLength") ? f.get("maxLength").asInt() : null));
        }
        return out;
    }

    private static Object literal(JsonNode n) {
        if (n.isBoolean()) {
            return n.asBoolean();
        }
        if (n.isIntegralNumber()) {
            return n.asLong();
        }
        return n.asText();
    }

    /** camelCase -> snake_case, the same derivation the generator applies. */
    static String snake(String camel) {
        return camel.replaceAll("([a-z0-9])([A-Z])", "$1_$2").toLowerCase();
    }
}
