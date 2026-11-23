package com.bank.platform.controlrecord.validate;

import com.bank.platform.controlrecord.Fixtures;
import org.junit.jupiter.api.Test;

import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;

class RecordValidatorTest {

    private final RecordValidator validator = new RecordValidator(Fixtures.controlRecord());

    private static Map<String, Object> valid() {
        Map<String, Object> body = new LinkedHashMap<>();
        body.put("accountId", "MSA-00000001");
        body.put("customerReference", "CUST-0001");
        body.put("currency", "BHD");
        body.put("status", "ACTIVE");
        body.put("contractType", "Mudarabah");
        body.put("balanceMinor", 1500L);
        body.put("psrIahShare", Map.of("numerator", 1, "denominator", 3));
        return body;
    }

    @Test
    void a_well_formed_record_has_no_violations() {
        assertThat(validator.validate(valid(), false)).isEmpty();
    }

    @Test
    void an_undeclared_field_is_rejected__this_is_what_additionalProperties_true_allowed() {
        Map<String, Object> body = valid();
        body.put("profitRate", 0.07);
        assertThat(validator.validate(body, false))
                .extracting(Violation::field, Violation::code)
                .containsExactly(org.assertj.core.groups.Tuple.tuple("profitRate", "UNKNOWN_FIELD"));
    }

    @Test
    void a_missing_required_field_is_rejected_on_initiate_but_not_on_update() {
        Map<String, Object> body = new HashMap<>(valid());
        body.remove("currency");
        assertThat(validator.validate(body, false))
                .anySatisfy(v -> assertThat(v.code()).isEqualTo("REQUIRED"));
        assertThat(validator.validate(body, true)).isEmpty();
    }

    @Test
    void a_status_outside_the_catalogs_enum_is_rejected() {
        Map<String, Object> body = valid();
        body.put("status", "FROZEN");
        assertThat(validator.validate(body, false))
                .anySatisfy(v -> assertThat(v.code()).isEqualTo("NOT_PERMITTED"));
    }

    @Test
    void a_const_field_may_only_hold_its_one_value() {
        Map<String, Object> body = valid();
        body.put("contractType", "Murabaha");
        assertThat(validator.validate(body, false))
                .anySatisfy(v -> assertThat(v.field()).isEqualTo("contractType"));
    }

    @Test
    void a_negative_nonNegative_amount_is_rejected() {
        Map<String, Object> body = valid();
        body.put("balanceMinor", -1L);
        assertThat(validator.validate(body, false))
                .anySatisfy(v -> assertThat(v.code()).isEqualTo("NEGATIVE"));
    }

    @Test
    void money_without_its_currency_is_rejected_on_initiate__minor_units_cannot_be_scaled() {
        Map<String, Object> body = new HashMap<>(valid());
        body.remove("currency");
        assertThat(validator.validate(body, false))
                .anySatisfy(v -> assertThat(v.code()).isEqualTo("NO_CURRENCY"));
    }

    @Test
    void an_amount_may_be_patched_without_resending_the_currency__the_stored_one_fixes_the_scale() {
        assertThat(validator.validate(Map.of("balanceMinor", 999L), true)).isEmpty();
    }

    @Test
    void but_a_malformed_currency_sent_with_the_patch_is_still_rejected() {
        assertThat(validator.validate(Map.of("balanceMinor", 999L, "currency", "kwd"), true))
                .anySatisfy(v -> assertThat(v.code()).isEqualTo("NOT_ISO4217"));
    }

    @Test
    void a_decimal_amount_is_rejected__there_is_no_decimal_type_on_the_wire() {
        Map<String, Object> body = valid();
        body.put("balanceMinor", 15.00);
        assertThat(validator.validate(body, false))
                .anySatisfy(v -> assertThat(v.code()).isEqualTo("NOT_INTEGER"));
    }

    @Test
    void a_ratio_sent_as_a_decimal_is_rejected() {
        Map<String, Object> body = valid();
        body.put("psrIahShare", 0.3333);
        assertThat(validator.validate(body, false))
                .anySatisfy(v -> assertThat(v.code()).isEqualTo("NOT_RATIO"));
    }

    @Test
    void a_denominator_past_maxDenominator_is_rejected_before_it_can_overflow() {
        Map<String, Object> body = valid();
        body.put("psrIahShare", Map.of("numerator", 1, "denominator", 1_000_001L));
        assertThat(validator.validate(body, false))
                .anySatisfy(v -> assertThat(v.code()).isEqualTo("DENOMINATOR_TOO_LARGE"));
    }

    @Test
    void a_malformed_currency_code_is_rejected() {
        Map<String, Object> body = valid();
        body.put("currency", "Bhd");
        assertThat(validator.validate(body, false))
                .anySatisfy(v -> assertThat(v.code()).isEqualTo("NOT_ISO4217"));
    }

    @Test
    void a_malformed_date_is_rejected() {
        Map<String, Object> body = valid();
        body.put("openedOn", "2026-13-45");
        assertThat(validator.validate(body, false))
                .anySatisfy(v -> assertThat(v.code()).isEqualTo("NOT_DATE"));
    }

    @Test
    void the_scaffolds_free_form_payload_is_now_fully_rejected() {
        // Exactly what every one of the 203 shallow services accepted and stored.
        Map<String, Object> anything = Map.of("properties", Map.of("whatever", "goes"));
        List<Violation> violations = validator.validate(anything, false);
        assertThat(violations).anySatisfy(v -> assertThat(v.code()).isEqualTo("UNKNOWN_FIELD"));
        assertThat(violations).anySatisfy(v -> assertThat(v.code()).isEqualTo("REQUIRED"));
    }
}
