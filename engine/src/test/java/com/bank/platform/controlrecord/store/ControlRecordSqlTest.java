package com.bank.platform.controlrecord.store;

import com.bank.platform.controlrecord.Fixtures;
import com.bank.platform.controlrecord.spec.ControlRecordSpec;
import com.bank.platform.controlrecord.spec.DomainSpec;
import org.junit.jupiter.api.Test;

import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class ControlRecordSqlTest {

    private final ControlRecordSpec spec = Fixtures.controlRecord();

    @Test
    void insert_names_the_tenant_first_and_expands_the_ratio_into_two_columns() {
        assertThat(ControlRecordSql.insert(spec)).isEqualTo(
                "INSERT INTO mudarabah_savings_account (tenant_id, account_id, customer_reference, "
                        + "currency, status, contract_type, balance_minor, psr_iah_share_numerator, "
                        + "psr_iah_share_denominator, opened_on) "
                        + "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)");
    }

    @Test
    void select_by_id_is_scoped_to_the_tenant() {
        assertThat(ControlRecordSql.selectById(spec)).isEqualTo(
                "SELECT account_id, customer_reference, currency, status, contract_type, "
                        + "balance_minor, psr_iah_share_numerator, psr_iah_share_denominator, opened_on "
                        + "FROM mudarabah_savings_account WHERE tenant_id = ? AND account_id = ?");
    }

    @Test
    void every_statement_the_engine_can_build_filters_on_tenant_id() {
        DomainSpec domain = Fixtures.domain();
        List<String> statements = List.of(
                ControlRecordSql.insert(spec),
                ControlRecordSql.selectById(spec),
                ControlRecordSql.selectAll(spec),
                ControlRecordSql.update(spec, List.of("status")),
                ControlRecordSql.selectBehaviourQualifier(domain.behaviourQualifiers().get(0), spec));
        assertThat(statements).allSatisfy(sql -> assertThat(sql).contains("tenant_id"));
        // and nothing but the INSERT mentions it as a column rather than a filter
        assertThat(statements.subList(1, statements.size()))
                .allSatisfy(sql -> assertThat(sql).contains("tenant_id = ?"));
    }

    @Test
    void placeholder_count_matches_the_column_count() {
        String insert = ControlRecordSql.insert(spec);
        long placeholders = insert.chars().filter(c -> c == '?').count();
        // one tenant + one per column, and the ratio contributes two
        assertThat(placeholders).isEqualTo(1 + spec.columns().size());
        assertThat(spec.columns()).hasSize(9);
    }

    @Test
    void a_behaviour_qualifier_is_keyed_by_its_parents_primary_key() {
        DomainSpec domain = Fixtures.domain();
        assertThat(ControlRecordSql.selectBehaviourQualifier(
                domain.behaviourQualifiers().get(0), spec)).isEqualTo(
                "SELECT agreement_id, psr_mudarib_share_numerator, psr_mudarib_share_denominator "
                        + "FROM profit_sharing_agreement WHERE tenant_id = ? AND account_id = ?");
    }

    @Test
    void an_update_that_writes_nothing_is_refused_rather_than_built() {
        assertThatThrownBy(() -> ControlRecordSql.update(spec, List.of()))
                .isInstanceOf(IllegalArgumentException.class);
    }
}
