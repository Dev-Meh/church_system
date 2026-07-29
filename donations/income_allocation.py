"""Income allocation percentages for the mapato na matumizi report."""

POSHO_PERCENT = 65
POSHO_DEDUCT_PERCENT = 10  # Taken from pastor stipend (posho)
JIMBO_SHARE_OF_DEDUCT = 60  # % of the 10% posho deduction
SEHEM_SHARE_OF_DEDUCT = 40  # % of the 10% posho deduction

OTHER_ALLOCATIONS = (
    ('Zaka ya Ofisi Kuu', 10),
    ('Elimu ya Vyuo', 5),
    ('Akiba Mafao ya Mchungaji', 5),
    ('Matumizi ya Kanisa', 15),
)


def _pct_of_total(base_percent, *factors):
    """Combine percentage factors into a single % of total income."""
    value = base_percent
    for factor in factors:
        value = value * factor / 100
    return value


def build_allocation_rows(total_mapato):
    """Build allocation rows including posho → jimbo/sehem split."""
    total = total_mapato or 0

    posho_gross = total * POSHO_PERCENT / 100
    posho_deduct = posho_gross * POSHO_DEDUCT_PERCENT / 100
    jimbo_amount = posho_deduct * JIMBO_SHARE_OF_DEDUCT / 100
    sehem_amount = posho_deduct * SEHEM_SHARE_OF_DEDUCT / 100
    posho_net = posho_gross - posho_deduct

    rows = [
        {
            'name': 'Posho ya Mchungaji (jumla)',
            'percent': POSHO_PERCENT,
            'amount': posho_gross,
            'indent': 0,
        },
        {
            'name': 'Jimbo (60% ya 10% ya Posho)',
            'percent': _pct_of_total(POSHO_PERCENT, POSHO_DEDUCT_PERCENT, JIMBO_SHARE_OF_DEDUCT),
            'amount': jimbo_amount,
            'indent': 1,
        },
        {
            'name': 'Sehem (40% ya 10% ya Posho)',
            'percent': _pct_of_total(POSHO_PERCENT, POSHO_DEDUCT_PERCENT, SEHEM_SHARE_OF_DEDUCT),
            'amount': sehem_amount,
            'indent': 1,
        },
        {
            'name': 'Posho halisi (kanisani)',
            'percent': _pct_of_total(POSHO_PERCENT, 100 - POSHO_DEDUCT_PERCENT),
            'amount': posho_net,
            'indent': 0,
            'emphasis': True,
        },
    ]

    for name, percent in OTHER_ALLOCATIONS:
        rows.append({
            'name': name,
            'percent': percent,
            'amount': total * percent / 100,
            'indent': 0,
        })

    return rows
