package com.bank.platform.controlrecord.spec;

import org.junit.jupiter.api.Test;

import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class FieldTypeTest {

    @Test
    void every_catalog_type_word_resolves() {
        List<String> words = List.of("id", "ref", "string", "enum", "bool", "int32", "int64",
                "money", "ratio", "currency", "countryCode", "date", "timestamp", "period", "array");
        assertThat(words).allSatisfy(w -> assertThat(FieldType.of(w).word()).isEqualTo(w));
        assertThat(FieldType.values()).hasSize(words.size());
    }

    @Test
    void an_unknown_type_is_rejected_not_degraded_to_a_string_column() {
        assertThatThrownBy(() -> FieldType.of("decimal"))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessageContaining("unknown catalog field type 'decimal'");
    }

    @Test
    void a_ratio_occupies_two_bigint_columns() {
        assertThat(FieldType.RATIO.composite()).isTrue();
        assertThat(FieldType.RATIO.columns("psr_iah_share")).containsExactly(
                new FieldType.Column("psr_iah_share_numerator", "BIGINT"),
                new FieldType.Column("psr_iah_share_denominator", "BIGINT"));
    }

    @Test
    void a_period_occupies_two_date_columns() {
        assertThat(FieldType.PERIOD.columns("hawl")).containsExactly(
                new FieldType.Column("hawl_from", "DATE"),
                new FieldType.Column("hawl_to", "DATE"));
    }

    @Test
    void money_is_one_bigint_of_minor_units() {
        assertThat(FieldType.MONEY.composite()).isFalse();
        assertThat(FieldType.MONEY.columns("balance_minor"))
                .containsExactly(new FieldType.Column("balance_minor", "BIGINT"));
    }
}
