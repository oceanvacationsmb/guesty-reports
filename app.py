# --- 3. CALCULATION ENGINE (WITH DATE FILTER) ---
all_owners_data = []
total_ov2 = 0

for name, settings in st.session_state.owner_db.items():
    owner_data = get_mimic_data(name)

    # ✅ FILTER BY SELECTED DATE RANGE
    owner_data = [
        r for r in owner_data
        if r["In"] <= end_date and r["Out"] >= start_date
    ]

    o_comm, o_cln, o_exp, o_fare = 0, 0, 0, 0

    for r in owner_data:
        f, c, e = r['Fare'], r['Cln'], r['Exp']
        comm = round(f * (settings['pct'] / 100), 2)

        o_comm += comm
        o_cln += c
        o_exp += e
        o_fare += f

    is_draft = settings['type'] == "DRAFT"

    if is_draft:
        top_rev = o_fare + o_cln
        net_rev = top_rev - o_cln - o_comm - o_exp
        draft_amt = o_comm + o_cln + o_exp
        ach_amt = 0
    else:
        top_rev = o_fare
        net_rev = o_fare - o_comm - o_exp
        draft_amt = 0
        ach_amt = net_rev

    all_owners_data.append({
        "OWNER": name,
        "TYPE": settings['type'],
        "REVENUE": top_rev,
        "PCT": settings['pct'],
        "COMM": o_comm,
        "EXP": o_exp,
        "CLN": o_cln,
        "NET": net_rev,
        "DRAFT": draft_amt,
        "ACH": ach_amt
    })

    total_ov2 += o_comm
