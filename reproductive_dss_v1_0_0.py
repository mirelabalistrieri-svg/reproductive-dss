import streamlit as st


# ============================================================
# DECISION ENGINE
# ============================================================

STRATEGIES = [
    "ReBreed21",
    "Resynch14",
    "Resynch22",
    "Resynch33",
]

DISPLAY_ORDER = [
    "ReBreed21",
    "Resynch14",
    "Resynch22",
    "Resynch33",
]

COELIGIBLE_OUTPUT = "ReBreed21 and Resynch14 co-eligible"
NO_ELIGIBLE_OUTPUT = "NO ELIGIBLE STRATEGY"


def evaluate_scenario(
    handling_infrastructure,
    doppler_available,
    field_team_availability,
    veterinary_availability,
    breeding_season_duration,
    number_of_females,
    historical_pregnancy_rate,
    calving_distribution,
):
    eligible = set(STRATEGIES)
    reasons = {strategy: [] for strategy in STRATEGIES}
    warnings = []

    def exclude(strategies, reason):
        for strategy in strategies:
            if strategy in eligible:
                eligible.remove(strategy)

            reasons[strategy].append(reason)

    # 1) Handling infrastructure
    if handling_infrastructure == "No":
        exclude(
            ["ReBreed21", "Resynch14"],
            "Inadequate handling infrastructure for compressed schedules "
            "excludes the super-early resynchronization strategies."
        )

    # 2) Doppler availability
    if doppler_available == "No":
        exclude(
            ["ReBreed21", "Resynch14"],
            "Doppler ultrasonography is required for the super-early "
            "strategies evaluated."
        )

    # 3) Field-team availability × herd size
    if field_team_availability == "Low":
        exclude(
            ["ReBreed21", "Resynch14", "Resynch22"],
            "Low field-team availability limits implementation to "
            "the Resynch33 strategy."
        )

    elif (
        field_team_availability == "Medium"
        and number_of_females == "Above 10,000"
    ):
        exclude(
            ["ReBreed21", "Resynch14"],
            "For herds above 10,000 females, medium field-team "
            "availability is insufficient for super-early program logistics."
        )

        warnings.append(
            "Large herd: implementation requires careful planning of "
            "animal flow, handling capacity, and labor allocation."
        )

    elif number_of_females == "Above 10,000":
        warnings.append(
            "Large herd: implementation requires careful planning of "
            "animal flow, handling capacity, and labor allocation."
        )

    # 4) Veterinary availability
    veterinary_allowed = {
        "Protocol start + device removal + AI": set(STRATEGIES),
        "Device removal + AI": {
            "ReBreed21",
            "Resynch14",
            "Resynch22",
        },
        "AI only": {"ReBreed21"},
        "Protocol start only": {"Resynch33"},
        "Device removal only": {
            "Resynch14",
            "Resynch22",
        },
    }

    allowed = veterinary_allowed[veterinary_availability]

    exclude(
        [
            strategy
            for strategy in STRATEGIES
            if strategy not in allowed
        ],
        f"Veterinary availability ({veterinary_availability}) "
        f"is incompatible with this strategy."
    )

    # 5) Breeding-season duration
    season_allowed = {
        "Short (≤60 days)": {
            "ReBreed21",
            "Resynch14",
        },
        "Medium (61–80 days)": {
            "Resynch22",
        },
        "Long (>80 days)": {
            "Resynch33",
        },
    }

    allowed = season_allowed[breeding_season_duration]

    exclude(
        [
            strategy
            for strategy in STRATEGIES
            if strategy not in allowed
        ],
        f"The {breeding_season_duration} breeding-season window is "
        f"incompatible with completing three AIs using this strategy."
    )

    # 6) Number of females
    # No standalone exclusion.
    # Its effect is represented by the interaction with field-team availability.

    # 7) Historical pregnancy rate
    if historical_pregnancy_rate == "Below 70%":
        exclude(
            ["ReBreed21", "Resynch14"],
            "A historical pregnancy rate below 70% indicates that more "
            "fundamental reproductive constraints should be addressed before "
            "adopting the super-early strategies evaluated in this DSS."
        )

    # 8) Calving distribution
    if calving_distribution == "40% / 30% / 30%":
        exclude(
            ["ReBreed21", "Resynch14"],
            "A 40/30/30 calving distribution excludes the super-early "
            "strategies because fewer cows may have an adequate postpartum "
            "interval before the subsequent breeding season."
        )

    elif calving_distribution in {
        "33% / 33% / 33%",
        "10% / 20% / 70%",
    }:
        exclude(
            ["ReBreed21", "Resynch14", "Resynch22"],
            f"Calving distribution ({calving_distribution}) limits "
            "eligibility to Resynch33 because a large proportion of cows "
            "calve late and may have an insufficient postpartum interval "
            "before the subsequent breeding season."
        )

    ordered_eligible = [
        strategy
        for strategy in DISPLAY_ORDER
        if strategy in eligible
    ]

    if not ordered_eligible:
        dss_output = NO_ELIGIBLE_OUTPUT

    elif set(ordered_eligible) == {"ReBreed21", "Resynch14"}:
        dss_output = COELIGIBLE_OUTPUT

    elif len(ordered_eligible) == 1:
        dss_output = ordered_eligible[0]

    else:
        raise ValueError(
            "Unexpected eligibility combination: "
            f"{ordered_eligible}"
        )

    return {
        "dss_output": dss_output,
        "eligible_strategies": ordered_eligible,
        "exclusion_reasons": reasons,
        "warnings": warnings,
    }


# ============================================================
# PRESENTATION DATA
# ============================================================

STRATEGY_INFO = {
    "ReBreed21": {
        "type": "Super-early resynchronization",
        "interval": "21-day reinsemination interval",
        "description": (
            "Provides the earliest reinsemination opportunity among "
            "the evaluated strategies."
        ),
    },
    "Resynch14": {
        "type": "Super-early resynchronization",
        "interval": "Approximately 24-day reinsemination interval",
        "description": (
            "Allows early identification and reinsemination of "
            "nonpregnant females."
        ),
    },
    "Resynch22": {
        "type": "Early resynchronization",
        "interval": "Approximately 32-day reinsemination interval",
        "description": (
            "Starts resynchronization before conventional pregnancy diagnosis."
        ),
    },
    "Resynch33": {
        "type": "Conventional resynchronization",
        "interval": "Approximately 42-day reinsemination interval",
        "description": (
            "Resynchronization begins after conventional pregnancy diagnosis."
        ),
    },
}


TIMELINES = {
    "ReBreed21": [
        ("D0", "TAI 1"),
        ("D12", "P4 device"),
        ("D19", "Device removal"),
        ("D21", "Doppler + TAI 2"),
        ("D33", "P4 device"),
        ("D40", "Device removal"),
        ("D42", "Doppler + TAI 3"),
    ],
    "Resynch14": [
        ("D0", "TAI 1"),
        ("D14", "P4 device"),
        ("D22", "Doppler + removal"),
        ("D24", "TAI 2"),
        ("D38", "P4 device"),
        ("D46", "Doppler + removal"),
        ("D48", "TAI 3"),
    ],
    "Resynch22": [
        ("D0", "TAI 1"),
        ("D22", "P4 device"),
        ("D30", "Pregnancy diagnosis"),
        ("D32", "TAI 2"),
        ("~D64", "TAI 3"),
    ],
    "Resynch33": [
        ("D0", "TAI 1"),
        ("~D33", "Pregnancy diagnosis"),
        ("~D42", "TAI 2"),
        ("~D84", "TAI 3"),
    ],
}


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Reproductive DSS",
    page_icon="🐄",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
    <style>
    .stApp {
        background-color: #f7faf8;
    }

    .block-container {
        max-width: 1450px;
        padding-top: 1.2rem;
        padding-bottom: 2rem;
    }

    h1, h2, h3 {
        color: #173f38;
    }

    section[data-testid="stSidebar"] {
        background: linear-gradient(
            180deg,
            #0f4b43 0%,
            #123f39 100%
        );
    }

    section[data-testid="stSidebar"] label {
        color: white !important;
        font-weight: 600 !important;
    }

    section[data-testid="stSidebar"] .stMarkdown p {
        color: white;
    }

    section[data-testid="stSidebar"]
    div[data-baseweb="select"] > div {
        background-color: white !important;
        border-radius: 8px !important;
    }

    section[data-testid="stSidebar"]
    div[data-baseweb="select"] span {
        color: #173f38 !important;
    }

    section[data-testid="stSidebar"]
    div[data-baseweb="select"] svg {
        fill: #173f38 !important;
    }

    div.stButton > button {
        width: 100%;
        min-height: 3rem;
        background-color: #238b57;
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 700;
    }

    div.stButton > button:hover {
        background-color: #1b7248;
        color: white;
        border: none;
    }

    .recommend-card {
        background: linear-gradient(
            120deg,
            #e7f6ec 0%,
            #f5fbf7 100%
        );
        border: 1px solid #cbe3d3;
        border-radius: 14px;
        padding: 1.5rem;
        min-height: 210px;
        box-shadow: 0 3px 12px rgba(0,0,0,0.03);
    }

    .recommend-label {
        color: #24764d;
        font-size: 0.9rem;
        font-weight: 700;
        margin-bottom: 0.4rem;
    }

    .recommend-title {
        color: #143f34;
        font-size: 2.5rem;
        font-weight: 800;
        margin-bottom: 0.2rem;
    }

    .recommend-type {
        color: #46645e;
        font-size: 1.05rem;
        font-weight: 600;
        margin-bottom: 0.9rem;
    }

    .recommend-text {
        color: #4f655f;
        font-size: 0.9rem;
        line-height: 1.5;
    }

    .footer {
        border-top: 1px solid #e0e8e4;
        margin-top: 1.5rem;
        padding-top: 0.8rem;
        font-size: 0.72rem;
        color: #78908a;
        display: flex;
        justify-content: space-between;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.markdown(
        '<h2 style="color: white;">🐄 Reproductive DSS</h2>',
        unsafe_allow_html=True,
    )

    st.caption(
        "Decision-support system for reproductive strategy "
        "selection in tropical beef cattle"
    )

    st.markdown("---")

    st.markdown(
        '<h3 style="color: white;">Farm inputs</h3>',
        unsafe_allow_html=True,
    )

    handling = st.selectbox(
        "Handling infrastructure for compressed schedules",
        ["Yes", "No"],
        help=(
            "Yes indicates that the facilities and animal-flow capacity "
            "allow the eligible group to be safely gathered, sorted, "
            "restrained, and processed within the shorter time windows "
            "required by ReBreed21 and Resynch14. No indicates that "
            "standard reproductive handling remains possible, but these "
            "compressed schedules cannot be safely or efficiently implemented."
        ),
    )

    doppler = st.selectbox(
        "Doppler ultrasonography",
        ["Yes", "No"],
    )

    team = st.selectbox(
        "Field-team availability",
        ["High", "Medium", "Low"],
        help=(
            "High: available for all scheduled procedures and able to process "
            "the herd within each time window. Medium: available for all "
            "procedures, but with limited capacity for compressed schedules in "
            "herds above 10,000 females. Low: unable to support one or more "
            "additional handling events required by early or super-early "
            "resynchronization."
        ),
    )

    vet = st.selectbox(
        "Veterinary availability",
        [
            "Protocol start + device removal + AI",
            "Device removal + AI",
            "AI only",
            "Protocol start only",
            "Device removal only",
        ],
    )

    season = st.selectbox(
        "Breeding-season duration",
        [
            "Short (≤60 days)",
            "Medium (61–80 days)",
            "Long (>80 days)",
        ],
    )

    herd = st.selectbox(
        "Number of females",
        [
            "Up to 500",
            "501 to 1,000",
            "1,001 to 10,000",
            "Above 10,000",
        ],
    )

    preg = st.selectbox(
        "Historical pregnancy rate",
        [
            "Below 70%",
            "70% to 80%",
            "Above 80%",
        ],
    )

    calving = st.selectbox(
        "Calving distribution",
        [
            "70% / 20% / 10%",
            "50% / 30% / 20%",
            "40% / 30% / 30%",
            "33% / 33% / 33%",
            "10% / 20% / 70%",
        ],
        help=(
            "Proportion of females calving in the first, second, and third "
            "thirds of the most recent calving season preceding the intended "
            "breeding season."
        ),
    )

    evaluate = st.button(
        "Evaluate strategy",
        type="primary",
        use_container_width=True,
    )


# ============================================================
# HEADER
# ============================================================

header_left, header_right = st.columns([3, 1])

with header_left:
    st.markdown("## Precision decisions for reproductive management")
    st.caption(
        "Rule-based DSS for reproductive strategy eligibility assessment"
    )

with header_right:
    st.markdown("**Laboratory of Animal Reproduction**")
    st.caption("ESALQ/USP")

st.divider()


# ============================================================
# TIMELINE FUNCTION
# ============================================================

def display_timeline(strategy):
    timeline = TIMELINES[strategy]
    timeline_columns = st.columns(len(timeline))

    for column, (day, event) in zip(timeline_columns, timeline):
        with column:
            st.markdown(
                f"""
                <div style="
                    text-align:center;
                    background:white;
                    border:1px solid #dce6e1;
                    border-radius:10px;
                    padding:0.8rem 0.4rem;
                    min-height:120px;
                ">
                    <div style="
                        width:16px;
                        height:16px;
                        background:#238b57;
                        border-radius:50%;
                        margin:0 auto 0.5rem auto;
                    "></div>
                    <div style="
                        font-weight:800;
                        color:#173f38;
                        font-size:0.85rem;
                    ">
                        {day}
                    </div>
                    <div style="
                        color:#6a817b;
                        font-size:0.72rem;
                        margin-top:0.3rem;
                    ">
                        {event}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


# ============================================================
# RESULT
# ============================================================

if evaluate:
    result = evaluate_scenario(
        handling,
        doppler,
        team,
        vet,
        season,
        herd,
        preg,
        calving,
    )

    dss_output = result["dss_output"]

    top_left, top_right = st.columns([1.7, 1], gap="large")

    with top_left:
        if dss_output == NO_ELIGIBLE_OUTPUT:
            st.error("No eligible strategy")

            st.write(
                "None of the evaluated reproductive strategies "
                "simultaneously satisfies all predefined eligibility "
                "requirements for three AI opportunities within the "
                "specified breeding season."
            )

        elif dss_output == COELIGIBLE_OUTPUT:
            st.markdown(
                """
                <div class="recommend-card">
                    <div class="recommend-label">
                        ✓ DSS output
                    </div>
                    <div class="recommend-title">
                        ReBreed21 and Resynch14
                    </div>
                    <div class="recommend-type">
                        Co-eligible strategies
                    </div>
                    <div class="recommend-text">
                        Both strategies satisfy all predefined eligibility
                        criteria for the reported farm scenario. The variables
                        included in the DSS do not support prioritization of
                        one strategy over the other.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        else:
            info = STRATEGY_INFO[dss_output]

            st.markdown(
                f"""
                <div class="recommend-card">
                    <div class="recommend-label">
                        ✓ DSS output
                    </div>
                    <div class="recommend-title">
                        {dss_output}
                    </div>
                    <div class="recommend-type">
                        {info["type"]}
                    </div>
                    <div class="recommend-text">
                        {info["description"]}<br><br>
                        This strategy satisfies all predefined eligibility
                        criteria for the reported farm scenario.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with top_right:
        st.markdown("### Farm scenario summary")

        st.metric(
            "Handling infrastructure for compressed schedules",
            handling,
        )
        st.metric("Doppler ultrasonography", doppler)
        st.metric("Field-team availability", team)
        st.metric("Veterinary availability", vet)
        st.metric("Breeding-season duration", season)
        st.metric("Number of females", herd)
        st.metric("Historical pregnancy rate", preg)
        st.metric("Calving distribution", calving)

    if dss_output != NO_ELIGIBLE_OUTPUT:
        st.markdown("### Why this output?")

        reason_cols = st.columns(3)

        if dss_output == COELIGIBLE_OUTPUT:
            with reason_cols[0]:
                st.success(
                    "All eligibility requirements for ReBreed21 "
                    "and Resynch14 are met."
                )

            with reason_cols[1]:
                st.success(
                    "Both strategies are compatible with the reported "
                    "reproductive and operational conditions."
                )

            with reason_cols[2]:
                st.success(
                    "ReBreed21: 21-day interval | "
                    "Resynch14: approximately 24-day interval"
                )

        else:
            with reason_cols[0]:
                st.success(
                    f"All eligibility requirements for {dss_output} are met."
                )

            with reason_cols[1]:
                st.success(
                    "Compatible with the reported reproductive and "
                    "operational conditions."
                )

            with reason_cols[2]:
                st.success(
                    STRATEGY_INFO[dss_output]["interval"]
                )

    st.markdown("### Eligibility assessment")

    col_eligible, col_excluded = st.columns(2, gap="large")

    with col_eligible:
        st.markdown("#### Eligible strategies")

        if result["eligible_strategies"]:
            for strategy_name in result["eligible_strategies"]:
                info = STRATEGY_INFO[strategy_name]

                with st.container(border=True):
                    st.markdown(f"**{strategy_name}**")
                    st.caption(
                        f'{info["type"]} | {info["interval"]}'
                    )

        else:
            st.info(
                "No reproductive strategy remains eligible "
                "for the current scenario."
            )

    with col_excluded:
        st.markdown("#### Excluded strategies")

        excluded = [
            strategy
            for strategy in STRATEGIES
            if strategy not in result["eligible_strategies"]
        ]

        if excluded:
            for strategy_name in excluded:
                with st.container(border=True):
                    st.markdown(f"**{strategy_name}**")

                    for reason in result["exclusion_reasons"][strategy_name]:
                        st.caption(f"• {reason}")

        else:
            st.info(
                "No strategies were excluded for the current scenario."
            )

    if result["warnings"]:
        st.markdown("### Operational considerations")

        for warning in result["warnings"]:
            st.warning(warning)

    if dss_output != NO_ELIGIBLE_OUTPUT:
        st.markdown("### Reproductive-management timeline")

        if dss_output == COELIGIBLE_OUTPUT:
            st.markdown("#### ReBreed21")
            display_timeline("ReBreed21")

            st.markdown("#### Resynch14")
            display_timeline("Resynch14")

        else:
            display_timeline(dss_output)


# ============================================================
# INITIAL SCREEN
# ============================================================

else:
    st.markdown("## Reproductive strategy decision support")

    st.write(
        "Select the eight farm-level variables in the sidebar "
        "and click **Evaluate strategy**."
    )

    st.info(
        "The DSS will identify the eligible strategy or strategies, "
        "explain exclusion criteria, and display the corresponding "
        "reproductive-management timeline."
    )


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    """
    <div class="footer">
        <div>
            Reproductive DSS | Public release 1.0.0
        </div>
        <div>
            Science into reproductive efficiency
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)