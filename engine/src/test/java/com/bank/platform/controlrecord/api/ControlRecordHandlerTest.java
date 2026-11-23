package com.bank.platform.controlrecord.api;

import com.bank.platform.controlrecord.Fixtures;
import com.bank.platform.controlrecord.spec.BehaviourQualifierSpec;
import com.bank.platform.controlrecord.spec.ControlRecordSpec;
import com.bank.platform.controlrecord.spec.DomainSpec;
import com.bank.platform.controlrecord.store.FakeStore;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;

class ControlRecordHandlerTest {

    private FakeStore store;
    private ControlRecordHandler handler;

    @BeforeEach
    void setUp() {
        store = new FakeStore();
        handler = new ControlRecordHandler(Fixtures.domain(), store, 50);
    }

    private static Map<String, Object> record() {
        Map<String, Object> body = new LinkedHashMap<>();
        body.put("accountId", "MSA-00000001");
        body.put("customerReference", "CUST-0001");
        body.put("currency", "KWD");
        body.put("status", "ACTIVE");
        body.put("contractType", "Mudarabah");
        body.put("balanceMinor", 250_000L);
        body.put("psrIahShare", Map.of("numerator", 1, "denominator", 3));
        return body;
    }


    @SuppressWarnings("unchecked")
    private static Map<String, Object> map(Object body) {
        return (Map<String, Object>) body;
    }

    @Test
    void service_domain_metadata_comes_from_the_catalog_not_from_hardcoded_strings() {
        ControlRecordHandler.Response response = handler.serviceDomain();
        assertThat(response.status()).isEqualTo(200);
        Map<String, Object> body = map(response.body());
        assertThat(body).containsEntry("serviceDomain", "Mudarabah Savings Account")
                .containsEntry("functionalPattern", "Fulfill")
                .containsEntry("fields", 8)
                .containsEntry("servedBy", "control-record-engine");
        assertThat(body.get("behaviourQualifiers")).isEqualTo(List.of("profit-sharing-agreement"));
        // and NOT the scaffold's "phase": "1-shallow"
        assertThat(body).doesNotContainKey("phase");
    }

    @Test
    void initiate_stores_a_valid_record_and_answers_201() {
        ControlRecordHandler.Response response = handler.initiate("tenant-a", record());
        assertThat(response.status()).isEqualTo(201);
        assertThat(store.findById("tenant-a", "MSA-00000001")).isPresent();
    }

    @Test
    void initiate_refuses_an_invalid_record_with_422_and_says_which_field() {
        Map<String, Object> bad = record();
        bad.put("status", "FROZEN");
        ControlRecordHandler.Response response = handler.initiate("tenant-a", bad);
        assertThat(response.status()).isEqualTo(422);
        Map<String, Object> body = map(response.body());
        assertThat(body).containsEntry("error", "VALIDATION_FAILED");
        assertThat((List<?>) body.get("violations")).hasSize(1);
        assertThat(store.findAll("tenant-a", 10)).isEmpty();
    }

    @Test
    void one_tenants_record_is_invisible_to_another() {
        handler.initiate("tenant-a", record());
        assertThat(handler.retrieve("tenant-b", "MSA-00000001").status()).isEqualTo(404);
        assertThat(handler.retrieve("tenant-a", "MSA-00000001").status()).isEqualTo(200);
        assertThat(handler.retrieveAll("tenant-b", null).body()).isEqualTo(List.of());
    }

    @Test
    void retrieve_of_an_unknown_id_is_404_and_leaks_nothing() {
        ControlRecordHandler.Response response = handler.retrieve("tenant-a", "MSA-99999999");
        assertThat(response.status()).isEqualTo(404);
        assertThat(((Map<?, ?>) response.body()).get("message")).isEqualTo("unknown control record id");
    }

    @Test
    void update_accepts_a_partial_patch_but_refuses_to_move_the_primary_key() {
        handler.initiate("tenant-a", record());
        assertThat(handler.update("tenant-a", "MSA-00000001", Map.of("status", "SUSPENDED")).status())
                .isEqualTo(200);
        ControlRecordHandler.Response moved =
                handler.update("tenant-a", "MSA-00000001", Map.of("accountId", "MSA-00000002"));
        assertThat(moved.status()).isEqualTo(400);
        assertThat(((Map<?, ?>) moved.body()).get("error")).isEqualTo("IMMUTABLE_ID");
    }

    @Test
    void update_of_an_unknown_id_is_404() {
        assertThat(handler.update("tenant-a", "nope", Map.of("status", "ACTIVE")).status())
                .isEqualTo(404);
    }

    @Test
    void control_actions_are_derived_from_the_domains_own_status_enum() {
        assertThat(handler.availableActions()).containsExactly("resume", "suspend", "terminate");
        handler.initiate("tenant-a", record());
        ControlRecordHandler.Response suspended =
                handler.control("tenant-a", "MSA-00000001", Map.of("action", "suspend"));
        assertThat(suspended.status()).isEqualTo(200);
        assertThat(((Map<?, ?>) suspended.body()).get("status")).isEqualTo("SUSPENDED");
    }

    @Test
    void an_action_the_domains_lifecycle_does_not_have_is_not_offered() {
        // A domain whose status enum has no SUSPENDED gets no suspend action —
        // the scaffold hardcoded all four statuses for all 203 domains.
        ControlRecordSpec noSuspend = new ControlRecordSpec("Fatwa Record", "fatwa_record", "fatwaId",
                List.of(Fixtures.field("fatwaId", com.bank.platform.controlrecord.spec.FieldType.ID, true),
                        Fixtures.enumField("status", true, List.of("DRAFT", "ACTIVE", "TERMINATED"))));
        DomainSpec domain = new DomainSpec("Fatwa And Ruling Repository", "fatwa-and-ruling-repository",
                "Catalog", "Fatwa", "Shariah Governance and Compliance", "Shariah Governance",
                noSuspend.name(), noSuspend, List.of());
        ControlRecordHandler limited = new ControlRecordHandler(domain, new FakeStore(), 50);
        assertThat(limited.availableActions()).containsExactly("resume", "terminate");
        limited.initiate("tenant-a", Map.of("fatwaId", "F-1", "status", "ACTIVE"));
        assertThat(limited.control("tenant-a", "F-1", Map.of("action", "suspend")).status())
                .isEqualTo(400);
    }

    @Test
    void an_unknown_control_action_is_400() {
        handler.initiate("tenant-a", record());
        ControlRecordHandler.Response response =
                handler.control("tenant-a", "MSA-00000001", Map.of("action", "freeze"));
        assertThat(response.status()).isEqualTo(400);
        assertThat(((Map<?, ?>) response.body()).get("error")).isEqualTo("UNKNOWN_ACTION");
    }

    @Test
    void a_behaviour_qualifier_is_served_only_for_a_record_that_exists() {
        store.qualifierRows.add(Map.of("agreementId", "PSA-1"));
        assertThat(handler.retrieveQualifier("tenant-a", "MSA-00000001", "profit-sharing-agreement")
                .status()).isEqualTo(404);
        handler.initiate("tenant-a", record());
        ControlRecordHandler.Response response =
                handler.retrieveQualifier("tenant-a", "MSA-00000001", "profit-sharing-agreement");
        assertThat(response.status()).isEqualTo(200);
        assertThat((List<?>) response.body()).hasSize(1);
    }

    @Test
    void an_undeclared_qualifier_path_is_404() {
        handler.initiate("tenant-a", record());
        assertThat(handler.retrieveQualifier("tenant-a", "MSA-00000001", "made-up").status())
                .isEqualTo(404);
    }

    @Test
    void retrieveAll_caps_the_page_size_at_the_configured_default() {
        ControlRecordHandler small = new ControlRecordHandler(Fixtures.domain(), store, 2);
        for (int i = 1; i <= 5; i++) {
            Map<String, Object> body = record();
            body.put("accountId", "MSA-0000000" + i);
            small.initiate("tenant-a", body);
        }
        assertThat((List<?>) small.retrieveAll("tenant-a", 1000).body()).hasSize(2);
    }

    @Test
    void a_qualifier_with_no_fields_is_not_a_route() {
        // The catalog names some qualifiers without giving them fields; those
        // get no table and no path, so they cannot be requested at all.
        DomainSpec domain = Fixtures.domain();
        assertThat(domain.behaviourQualifiers()).extracting(BehaviourQualifierSpec::path)
                .doesNotContain("screening-reason-code");
    }
}
