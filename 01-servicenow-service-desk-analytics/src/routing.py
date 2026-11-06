"""Test whether simple assignment rules would send tickets to the right group first time.

Approach
  1. Split incidents by open date: the first 60% train, the last 40% test (no leakage
     from the future into the rules).
  2. In training, for each subcategory, find the group that most often resolved it.
  3. Keep a rule only where it clearly beats current routing in training
     (n >= 30 and at least +15 points of first-touch accuracy).
  4. Measure the kept rules on the test period only.
"""
import pandas as pd

MIN_N, MIN_LIFT = 30, 0.15


def evaluate(inc: pd.DataFrame) -> dict:
    d = inc.dropna(subset=["first_group", "resolving_group", "subcategory"]).sort_values("opened_at")
    cut = d.opened_at.quantile(0.6)
    train, test = d[d.opened_at <= cut], d[d.opened_at > cut]

    def first_touch(df):
        return (df.first_group == df.resolving_group).mean()

    stats = train.groupby("subcategory").agg(
        n=("number", "size"),
        current=("first_group", lambda s: first_touch(train.loc[s.index])),
        rule_group=("resolving_group", lambda s: s.mode().iat[0]),
    )
    stats["rule_acc"] = [
        (train.loc[train.subcategory == sc, "resolving_group"] == g).mean()
        for sc, g in stats.rule_group.items()
    ]
    rules = stats[(stats.n >= MIN_N) & (stats.rule_acc - stats.current >= MIN_LIFT)]

    covered = test[test.subcategory.isin(rules.index)].copy()
    covered["rule_group"] = covered.subcategory.map(rules.rule_group)
    before = covered.first_group == covered.resolving_group
    after = covered.rule_group == covered.resolving_group

    # What if we routed *everything* by subcategory? Check it against tickets that are routed right today.
    all_rules = stats.rule_group
    right_today = test[test.first_group == test.resolving_group]
    naive_agree = (right_today.subcategory.map(all_rules) == right_today.resolving_group).mean()

    return {
        "split_at": str(cut),
        "rules": rules.reset_index()[["subcategory", "rule_group", "n", "current", "rule_acc"]],
        "test_incidents": len(test),
        "covered": len(covered),
        "accuracy_before": before.mean(),
        "accuracy_after": after.mean(),
        "fixed": int((~before & after).sum()),
        "broken": int((before & ~after).sum()),
        "naive_agreement_on_correct": naive_agree,
    }
