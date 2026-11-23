package com.bank.platform.controlrecord.spec;

import org.junit.jupiter.api.Test;

import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;

/**
 * Reads the REAL catalog, not a fixture.
 *
 * This is the test that decides whether the engine can replace the generated
 * Java: if every one of the catalog's service domains loads into a spec, then
 * every one of them can be served without a line of per-domain code. A
 * fixture could never tell us that — the estate's own history shows a spike on
 * one simple domain returning a confidently wrong verdict about all of them.
 */
class CatalogReaderTest {

    private static final Path CATALOG =
            Path.of("..", "catalog", "islamic-service-landscape.json");

    private Map<String, DomainSpec> catalog() throws IOException {
        assertThat(CATALOG).as("the catalog this engine is driven by").exists();
        try (InputStream in = Files.newInputStream(CATALOG)) {
            return CatalogReader.readAll(in);
        }
    }

    @Test
    void every_service_domain_in_the_catalog_loads() throws IOException {
        Map<String, DomainSpec> domains = catalog();
        assertThat(domains).hasSizeGreaterThanOrEqualTo(48);
        assertThat(domains).allSatisfy((slug, domain) -> {
            assertThat(domain.controlRecord().fields()).as(slug + " has fields").isNotEmpty();
            assertThat(domain.controlRecord().primaryKeyField().type())
                    .as(slug + " primary key is an id").isEqualTo(FieldType.ID);
            assertThat(domain.controlRecordSlug()).as(slug + " control-record slug")
                    .matches("^[a-z0-9][a-z0-9-]*$");
        });
    }

    @Test
    void the_whole_catalog_maps_onto_the_closed_type_vocabulary() throws IOException {
        long fields = catalog().values().stream()
                .mapToLong(d -> d.controlRecord().fields().size()
                        + d.behaviourQualifiers().stream().mapToLong(b -> b.fields().size()).sum())
                .sum();
        // 2,813 fields across the catalog at the time of writing; the point is
        // that FieldType.of() threw for none of them.
        assertThat(fields).isGreaterThan(2_000L);
    }

    @Test
    void a_known_domain_reads_the_way_its_catalog_entry_declares() throws IOException {
        DomainSpec mudarabah = catalog().get("mudarabah-savings-account");
        assertThat(mudarabah).isNotNull();
        assertThat(mudarabah.controlRecord().table()).isEqualTo("mudarabah_savings_account");
        assertThat(mudarabah.controlRecord().primaryKey()).isEqualTo("accountId");
        assertThat(mudarabah.controlRecord().statusField()).isPresent();
        assertThat(mudarabah.behaviourQualifiers()).extracting(BehaviourQualifierSpec::path)
                .contains("profit-sharing-agreement");
        assertThat(mudarabah.readScope()).isEqualTo("isb:mudarabah-savings-account:read");
    }

    @Test
    void every_ratio_in_the_catalog_carries_the_bound_that_keeps_it_inside_int64() throws IOException {
        assertThat(catalog().values()).allSatisfy(domain ->
                assertThat(domain.controlRecord().fields().stream()
                        .filter(f -> f.type() == FieldType.RATIO))
                        .allSatisfy(f -> assertThat(f.maxDenominator())
                                .as(domain.slug() + "." + f.name() + " maxDenominator")
                                .isNotNull()));
    }

    @Test
    void camel_case_becomes_snake_case_the_same_way_the_generator_does_it() {
        assertThat(CatalogReader.snake("balanceMinor")).isEqualTo("balance_minor");
        assertThat(CatalogReader.snake("psrIahShare")).isEqualTo("psr_iah_share");
        assertThat(CatalogReader.snake("accountId")).isEqualTo("account_id");
        assertThat(CatalogReader.snake("status")).isEqualTo("status");
    }
}
