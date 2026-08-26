
    const tableStates = {
        'day-table': { currentPage: 1, pageSize: 25, allRows: [], filteredRows: [] },
        'eco-table': { currentPage: 1, pageSize: 10, allRows: [], filteredRows: [] },
        'earn-table': { currentPage: 1, pageSize: 10, allRows: [], filteredRows: [] },
        'analyst-table': { currentPage: 1, pageSize: 10, allRows: [], filteredRows: [] },
        'options-table': { currentPage: 1, pageSize: 10, allRows: [], filteredRows: [] },
        'portfolio-table': { currentPage: 1, pageSize: 25, allRows: [], filteredRows: [] }
    };

    window.portfolioData = {"account_number": "264695485", "account_name": "Traditional IRA", "last_updated": "2026-08-24 13:28:04 ET", "total_nav": 336871.01, "cash_balance": 70830.35, "equity_value": 266040.66, "risk_budget_pct": 0.75, "positions_count": 73, "positions": [{"symbol": "MU", "raw_symbol": "MU", "description": "MICRON TECHNOLOGY INC COM", "is_option": false, "quantity": 24.088, "last_price": 917.56, "current_value": 22102.19, "cost_basis_total": 13686.24, "average_cost": 568.18, "today_pnl_dollar": -1185.62, "today_pnl_pct": -5.1, "total_pnl_dollar": 8415.95, "total_pnl_pct": 61.49, "account_type": "Cash", "strategy_tag": "Tactical Momentum", "stop_loss": 853.33, "target_price": 1055.19, "entry_date": "Aug 24, 2026", "notes": "", "weight_pct": 6.56}, {"symbol": "COST", "raw_symbol": "COST", "description": "COSTCO WHOLESALE CORP COM", "is_option": false, "quantity": 20.508, "last_price": 969.01, "current_value": 19872.46, "cost_basis_total": 17730.93, "average_cost": 864.59, "today_pnl_dollar": 436.2, "today_pnl_pct": 2.24, "total_pnl_dollar": 2141.53, "total_pnl_pct": 12.08, "account_type": "Cash", "strategy_tag": "Tactical Momentum", "stop_loss": 901.18, "target_price": 1114.36, "entry_date": "Aug 24, 2026", "notes": "", "weight_pct": 5.9}, {"symbol": "PLTR", "raw_symbol": "PLTR", "description": "PALANTIR TECHNOLOGIES INC CL A", "is_option": false, "quantity": 100.0, "last_price": 177.435, "current_value": 17743.5, "cost_basis_total": 11476.6, "average_cost": 114.77, "today_pnl_dollar": -250.5, "today_pnl_pct": -1.4, "total_pnl_dollar": 6266.9, "total_pnl_pct": 54.61, "account_type": "Cash", "strategy_tag": "Core Long Holding", "stop_loss": 165.01, "target_price": 204.05, "entry_date": "Aug 24, 2026", "notes": "", "weight_pct": 5.27}, {"symbol": "SMH", "raw_symbol": "SMH", "description": "VANECK ETF TRUST SEMICONDUCTR ETF", "is_option": false, "quantity": 30.333, "last_price": 547.56, "current_value": 16609.14, "cost_basis_total": 6554.43, "average_cost": 216.08, "today_pnl_dollar": -390.09, "today_pnl_pct": -2.3, "total_pnl_dollar": 10054.71, "total_pnl_pct": 153.4, "account_type": "Cash", "strategy_tag": "Tactical Momentum", "stop_loss": 509.23, "target_price": 629.69, "entry_date": "Aug 24, 2026", "notes": "", "weight_pct": 4.93}, {"symbol": "SPMO", "raw_symbol": "SPMO", "description": "INVESCO EXCH TRADED FD TR II S&P 500 MOMNTM", "is_option": false, "quantity": 80.72, "last_price": 146.475, "current_value": 11823.46, "cost_basis_total": 9076.95, "average_cost": 112.45, "today_pnl_dollar": -182.03, "today_pnl_pct": -1.52, "total_pnl_dollar": 2746.51, "total_pnl_pct": 30.26, "account_type": "Cash", "strategy_tag": "Core Long Holding", "stop_loss": 136.22, "target_price": 168.45, "entry_date": "Aug 24, 2026", "notes": "", "weight_pct": 3.51}, {"symbol": "SOXL", "raw_symbol": "SOXL", "description": "DIREXION SHARES ETF TRUST DAILY SEMICONDUCTOR BULL 3X ETF", "is_option": false, "quantity": 100.709, "last_price": 111.2, "current_value": 11198.84, "cost_basis_total": 12305.51, "average_cost": 122.19, "today_pnl_dollar": -946.67, "today_pnl_pct": -7.8, "total_pnl_dollar": -1106.67, "total_pnl_pct": -8.99, "account_type": "Financing", "strategy_tag": "Core Long Holding", "stop_loss": 103.42, "target_price": 127.88, "entry_date": "Aug 24, 2026", "notes": "", "weight_pct": 3.32}, {"symbol": "HOOD", "raw_symbol": "HOOD", "description": "ROBINHOOD MKTS INC COM CL A", "is_option": false, "quantity": 100.0, "last_price": 108.02, "current_value": 10802.0, "cost_basis_total": 9799.9, "average_cost": 98.0, "today_pnl_dollar": -11.0, "today_pnl_pct": -0.11, "total_pnl_dollar": 1002.1, "total_pnl_pct": 10.23, "account_type": "Cash", "strategy_tag": "Core Long Holding", "stop_loss": 100.46, "target_price": 124.22, "entry_date": "Aug 24, 2026", "notes": "", "weight_pct": 3.21}, {"symbol": "SNDK", "raw_symbol": "SNDK", "description": "SANDISK CORP COM", "is_option": false, "quantity": 7.0, "last_price": 1508.91, "current_value": 10562.37, "cost_basis_total": 7827.89, "average_cost": 1118.27, "today_pnl_dollar": -610.19, "today_pnl_pct": -5.47, "total_pnl_dollar": 2734.48, "total_pnl_pct": 34.93, "account_type": "Cash", "strategy_tag": "Tactical Momentum", "stop_loss": 1403.29, "target_price": 1735.25, "entry_date": "Aug 24, 2026", "notes": "", "weight_pct": 3.14}, {"symbol": "NVDA", "raw_symbol": "NVDA", "description": "NVIDIA CORPORATION COM", "is_option": false, "quantity": 50.037, "last_price": 210.43, "current_value": 10529.29, "cost_basis_total": 8212.27, "average_cost": 164.12, "today_pnl_dollar": -214.66, "today_pnl_pct": -2.0, "total_pnl_dollar": 2317.02, "total_pnl_pct": 28.21, "account_type": "Cash", "strategy_tag": "Core Long Holding", "stop_loss": 195.7, "target_price": 241.99, "entry_date": "Aug 24, 2026", "notes": "", "weight_pct": 3.13}, {"symbol": "QQQ", "raw_symbol": "QQQ", "description": "INVESCO QQQ TR UNIT SER 1", "is_option": false, "quantity": 12.228, "last_price": 708.445, "current_value": 8662.87, "cost_basis_total": 6139.35, "average_cost": 502.07, "today_pnl_dollar": -61.08, "today_pnl_pct": -0.71, "total_pnl_dollar": 2523.52, "total_pnl_pct": 41.1, "account_type": "Cash", "strategy_tag": "Tactical Momentum", "stop_loss": 658.85, "target_price": 814.71, "entry_date": "Aug 24, 2026", "notes": "", "weight_pct": 2.57}, {"symbol": "BE", "raw_symbol": "BE", "description": "BLOOM ENERGY CORP COM CL A", "is_option": false, "quantity": 40.0, "last_price": 204.97, "current_value": 8198.8, "cost_basis_total": 7514.48, "average_cost": 187.86, "today_pnl_dollar": 140.8, "today_pnl_pct": 1.74, "total_pnl_dollar": 684.32, "total_pnl_pct": 9.11, "account_type": "Cash", "strategy_tag": "Tactical Momentum", "stop_loss": 190.62, "target_price": 235.72, "entry_date": "Aug 24, 2026", "notes": "", "weight_pct": 2.43}, {"symbol": "META", "raw_symbol": "META", "description": "META PLATFORMS INC CLASS A COMMON STOCK", "is_option": false, "quantity": 11.058, "last_price": 555.1, "current_value": 6138.3, "cost_basis_total": 7417.26, "average_cost": 670.76, "today_pnl_dollar": 57.5, "today_pnl_pct": 0.94, "total_pnl_dollar": -1278.96, "total_pnl_pct": -17.24, "account_type": "Cash", "strategy_tag": "Tactical Momentum", "stop_loss": 516.24, "target_price": 638.37, "entry_date": "Aug 24, 2026", "notes": "", "weight_pct": 1.82}, {"symbol": "COPX", "raw_symbol": "COPX", "description": "GLOBAL X FDS GLOBAL X COPPER", "is_option": false, "quantity": 64.211, "last_price": 94.26, "current_value": 6052.53, "cost_basis_total": 5165.52, "average_cost": 80.45, "today_pnl_dollar": -21.19, "today_pnl_pct": -0.35, "total_pnl_dollar": 887.01, "total_pnl_pct": 17.17, "account_type": "Cash", "strategy_tag": "Tactical Momentum", "stop_loss": 87.66, "target_price": 108.4, "entry_date": "Aug 24, 2026", "notes": "", "weight_pct": 1.8}, {"symbol": "GOOGL", "raw_symbol": "GOOGL", "description": "ALPHABET INC CAP STK CL A", "is_option": false, "quantity": 17.107, "last_price": 351.03, "current_value": 6005.07, "cost_basis_total": 5303.03, "average_cost": 309.99, "today_pnl_dollar": 106.23, "today_pnl_pct": 1.8, "total_pnl_dollar": 702.04, "total_pnl_pct": 13.24, "account_type": "Cash", "strategy_tag": "Tactical Momentum", "stop_loss": 326.46, "target_price": 403.68, "entry_date": "Aug 24, 2026", "notes": "", "weight_pct": 1.78}, {"symbol": "AXP", "raw_symbol": "AXP", "description": "AMERICAN EXPRESS CO COM USD0.20", "is_option": false, "quantity": 15.448, "last_price": 338.295, "current_value": 5225.98, "cost_basis_total": 3628.88, "average_cost": 234.91, "today_pnl_dollar": 35.45, "today_pnl_pct": 0.68, "total_pnl_dollar": 1597.1, "total_pnl_pct": 44.01, "account_type": "Cash", "strategy_tag": "Tactical Momentum", "stop_loss": 314.61, "target_price": 389.04, "entry_date": "Aug 24, 2026", "notes": "", "weight_pct": 1.55}, {"symbol": "GLDM", "raw_symbol": "GLDM", "description": "WORLD GOLD TR SPDR GLD MINIS", "is_option": false, "quantity": 50.0, "last_price": 92.21, "current_value": 4610.5, "cost_basis_total": 4796.98, "average_cost": 95.94, "today_pnl_dollar": 44.5, "today_pnl_pct": 0.97, "total_pnl_dollar": -186.48, "total_pnl_pct": -3.89, "account_type": "Cash", "strategy_tag": "Tactical Momentum", "stop_loss": 85.76, "target_price": 106.04, "entry_date": "Aug 24, 2026", "notes": "", "weight_pct": 1.37}, {"symbol": "WDC", "raw_symbol": "WDC", "description": "WESTERN DIGITAL CORP. COM", "is_option": false, "quantity": 10.009, "last_price": 436.41, "current_value": 4368.03, "cost_basis_total": 3747.89, "average_cost": 374.45, "today_pnl_dollar": -230.51, "today_pnl_pct": -5.02, "total_pnl_dollar": 620.14, "total_pnl_pct": 16.55, "account_type": "Cash", "strategy_tag": "Tactical Momentum", "stop_loss": 405.86, "target_price": 501.87, "entry_date": "Aug 24, 2026", "notes": "", "weight_pct": 1.3}, {"symbol": "FLKR", "raw_symbol": "FLKR", "description": "FRANKLIN TEMPLETON ETF TR FTSE SOUTH KOREA", "is_option": false, "quantity": 70.348, "last_price": 57.42, "current_value": 4039.38, "cost_basis_total": 3022.6, "average_cost": 42.97, "today_pnl_dollar": -75.98, "today_pnl_pct": -1.85, "total_pnl_dollar": 1016.78, "total_pnl_pct": 33.64, "account_type": "Cash", "strategy_tag": "Tactical Momentum", "stop_loss": 53.4, "target_price": 66.03, "entry_date": "Aug 24, 2026", "notes": "", "weight_pct": 1.2}, {"symbol": "PANW", "raw_symbol": "PANW", "description": "PALO ALTO NETWORKS INC COM USD0.0001", "is_option": false, "quantity": 11.0, "last_price": 349.9, "current_value": 3848.9, "cost_basis_total": 3790.82, "average_cost": 344.62, "today_pnl_dollar": -87.67, "today_pnl_pct": -2.23, "total_pnl_dollar": 58.08, "total_pnl_pct": 1.53, "account_type": "Margin", "strategy_tag": "Tactical Momentum", "stop_loss": 325.41, "target_price": 402.38, "entry_date": "Aug 24, 2026", "notes": "", "weight_pct": 1.14}, {"symbol": "AMD", "raw_symbol": "AMD", "description": "ADVANCED MICRO DEVICES INC", "is_option": false, "quantity": 8.0, "last_price": 459.795, "current_value": 3678.36, "cost_basis_total": 3617.76, "average_cost": 452.22, "today_pnl_dollar": -107.64, "today_pnl_pct": -2.85, "total_pnl_dollar": 60.6, "total_pnl_pct": 1.68, "account_type": "Cash", "strategy_tag": "Tactical Momentum", "stop_loss": 427.61, "target_price": 528.76, "entry_date": "Aug 24, 2026", "notes": "", "weight_pct": 1.09}, {"symbol": "MSFT", "raw_symbol": "MSFT", "description": "MICROSOFT CORP", "is_option": false, "quantity": 7.107, "last_price": 488.9183, "current_value": 3474.74, "cost_basis_total": 3090.27, "average_cost": 434.82, "today_pnl_dollar": 40.35, "today_pnl_pct": 1.17, "total_pnl_dollar": 384.47, "total_pnl_pct": 12.44, "account_type": "Cash", "strategy_tag": "Tactical Momentum", "stop_loss": 454.69, "target_price": 562.26, "entry_date": "Aug 24, 2026", "notes": "", "weight_pct": 1.03}, {"symbol": "MAGS", "raw_symbol": "MAGS", "description": "LISTED FD TR ROUNDHILL MAGNIF", "is_option": false, "quantity": 50.442, "last_price": 67.565, "current_value": 3408.11, "cost_basis_total": 2906.6, "average_cost": 57.62, "today_pnl_dollar": 14.37, "today_pnl_pct": 0.42, "total_pnl_dollar": 501.51, "total_pnl_pct": 17.25, "account_type": "Cash", "strategy_tag": "Tactical Momentum", "stop_loss": 62.84, "target_price": 77.7, "entry_date": "Aug 24, 2026", "notes": "", "weight_pct": 1.01}, {"symbol": "SILJ", "raw_symbol": "SILJ", "description": "AMPLIFY ETF TR AMPLIFY JUNIOR S", "is_option": false, "quantity": 102.934, "last_price": 31.88, "current_value": 3281.54, "cost_basis_total": 2179.0, "average_cost": 21.17, "today_pnl_dollar": -5.15, "today_pnl_pct": -0.16, "total_pnl_dollar": 1102.54, "total_pnl_pct": 50.6, "account_type": "Cash", "strategy_tag": "Tactical Momentum", "stop_loss": 29.65, "target_price": 36.66, "entry_date": "Aug 24, 2026", "notes": "", "weight_pct": 0.97}, {"symbol": "TTMI", "raw_symbol": "TTMI", "description": "TTM TECHNOLOGIES INC", "is_option": false, "quantity": 30.0, "last_price": 107.2471, "current_value": 3217.41, "cost_basis_total": 2519.55, "average_cost": 83.99, "today_pnl_dollar": -98.79, "today_pnl_pct": -2.98, "total_pnl_dollar": 697.86, "total_pnl_pct": 27.7, "account_type": "Cash", "strategy_tag": "Tactical Momentum", "stop_loss": 99.74, "target_price": 123.33, "entry_date": "Aug 24, 2026", "notes": "", "weight_pct": 0.96}, {"symbol": "IWM", "raw_symbol": "IWM", "description": "ISHARES RUSSELL 2000 ETF", "is_option": false, "quantity": 10.226, "last_price": 298.14, "current_value": 3048.78, "cost_basis_total": 2121.0, "average_cost": 207.41, "today_pnl_dollar": -18.62, "today_pnl_pct": -0.61, "total_pnl_dollar": 927.78, "total_pnl_pct": 43.74, "account_type": "Cash", "strategy_tag": "Tactical Momentum", "stop_loss": 277.27, "target_price": 342.86, "entry_date": "Aug 24, 2026", "notes": "", "weight_pct": 0.91}, {"symbol": "NBIS", "raw_symbol": "NBIS", "description": "NEBIUS GROUP N V COM USD0.01 CL A", "is_option": false, "quantity": 14.0, "last_price": 211.24, "current_value": 2957.36, "cost_basis_total": 3080.0, "average_cost": 220.0, "today_pnl_dollar": -110.46, "today_pnl_pct": -3.61, "total_pnl_dollar": -122.64, "total_pnl_pct": -3.98, "account_type": "Margin", "strategy_tag": "Tactical Momentum", "stop_loss": 196.45, "target_price": 242.93, "entry_date": "Aug 24, 2026", "notes": "", "weight_pct": 0.88}, {"symbol": "MU", "raw_symbol": "MU", "description": "MICRON TECHNOLOGY INC COM", "is_option": false, "quantity": 3.0, "last_price": 917.56, "current_value": 2752.68, "cost_basis_total": 2415.0, "average_cost": 805.0, "today_pnl_dollar": -147.66, "today_pnl_pct": -5.1, "total_pnl_dollar": 337.68, "total_pnl_pct": 13.98, "account_type": "Margin", "strategy_tag": "Tactical Momentum", "stop_loss": 853.33, "target_price": 1055.19, "entry_date": "Aug 24, 2026", "notes": "", "weight_pct": 0.82}, {"symbol": "MRVL", "raw_symbol": "MRVL", "description": "MARVELL TECHNOLOGY INC COM", "is_option": false, "quantity": 12.02, "last_price": 228.71, "current_value": 2749.09, "cost_basis_total": 3433.06, "average_cost": 285.61, "today_pnl_dollar": -100.13, "today_pnl_pct": -3.52, "total_pnl_dollar": -683.97, "total_pnl_pct": -19.92, "account_type": "Cash", "strategy_tag": "Tactical Momentum", "stop_loss": 212.7, "target_price": 263.02, "entry_date": "Aug 24, 2026", "notes": "", "weight_pct": 0.82}, {"symbol": "BBDC", "raw_symbol": "BBDC", "description": "BARINGS BDC INC COM", "is_option": false, "quantity": 232.426, "last_price": 9.405, "current_value": 2185.97, "cost_basis_total": 0.0, "average_cost": 0.0, "today_pnl_dollar": 15.1, "today_pnl_pct": 0.69, "total_pnl_dollar": 2185.96, "total_pnl_pct": 0.0, "account_type": "Cash", "strategy_tag": "Tactical Momentum", "stop_loss": 8.75, "target_price": 10.82, "entry_date": "Aug 24, 2026", "notes": "", "weight_pct": 0.65}, {"symbol": "IONQ", "raw_symbol": "IONQ", "description": "IONQ INC COM", "is_option": false, "quantity": 50.0, "last_price": 42.31, "current_value": 2115.5, "cost_basis_total": 1900.0, "average_cost": 38.0, "today_pnl_dollar": -127.5, "today_pnl_pct": -5.69, "total_pnl_dollar": 215.5, "total_pnl_pct": 11.34, "account_type": "Cash", "strategy_tag": "Tactical Momentum", "stop_loss": 39.35, "target_price": 48.66, "entry_date": "Aug 24, 2026", "notes": "", "weight_pct": 0.63}, {"symbol": "HPE", "raw_symbol": "HPE", "description": "HEWLETT PACKARD ENTERPRISE CO COM", "is_option": false, "quantity": 40.0, "last_price": 52.37, "current_value": 2094.8, "cost_basis_total": 1778.0, "average_cost": 44.45, "today_pnl_dollar": -43.2, "today_pnl_pct": -2.03, "total_pnl_dollar": 316.8, "total_pnl_pct": 17.82, "account_type": "Margin", "strategy_tag": "Tactical Momentum", "stop_loss": 48.7, "target_price": 60.23, "entry_date": "Aug 24, 2026", "notes": "", "weight_pct": 0.62}, {"symbol": "GDXJ", "raw_symbol": "GDXJ", "description": "VANECK ETF TRUST JUNIOR GOLD MINE", "is_option": false, "quantity": 15.676, "last_price": 132.84, "current_value": 2082.4, "cost_basis_total": 1451.4, "average_cost": 92.59, "today_pnl_dollar": 3.91, "today_pnl_pct": 0.18, "total_pnl_dollar": 631.0, "total_pnl_pct": 43.48, "account_type": "Cash", "strategy_tag": "Tactical Momentum", "stop_loss": 123.54, "target_price": 152.77, "entry_date": "Aug 24, 2026", "notes": "", "weight_pct": 0.62}, {"symbol": "MXL", "raw_symbol": "MXL", "description": "MAXLINEAR INC COM", "is_option": false, "quantity": 30.0, "last_price": 63.15, "current_value": 1894.5, "cost_basis_total": 2190.6, "average_cost": 73.02, "today_pnl_dollar": -103.8, "today_pnl_pct": -5.2, "total_pnl_dollar": -296.1, "total_pnl_pct": -13.52, "account_type": "Cash", "strategy_tag": "Tactical Momentum", "stop_loss": 58.73, "target_price": 72.62, "entry_date": "Aug 24, 2026", "notes": "", "weight_pct": 0.56}, {"symbol": "ASML", "raw_symbol": "ASML", "description": "ASML HOLDING NV EUR0.09 NY REGISTRY SHS 2012", "is_option": false, "quantity": 1.057, "last_price": 1746.185, "current_value": 1845.72, "cost_basis_total": 571.57, "average_cost": 540.75, "today_pnl_dollar": -18.58, "today_pnl_pct": -1.0, "total_pnl_dollar": 1274.15, "total_pnl_pct": 222.92, "account_type": "Cash", "strategy_tag": "Tactical Momentum", "stop_loss": 1623.95, "target_price": 2008.11, "entry_date": "Aug 24, 2026", "notes": "", "weight_pct": 0.55}, {"symbol": "FCEL", "raw_symbol": "FCEL", "description": "FUELCELL ENERGY INC COM NEW", "is_option": false, "quantity": 100.0, "last_price": 18.32, "current_value": 1832.0, "cost_basis_total": 2109.5, "average_cost": 21.1, "today_pnl_dollar": -122.0, "today_pnl_pct": -6.25, "total_pnl_dollar": -277.5, "total_pnl_pct": -13.15, "account_type": "Margin", "strategy_tag": "Tactical Momentum", "stop_loss": 17.04, "target_price": 21.07, "entry_date": "Aug 24, 2026", "notes": "", "weight_pct": 0.54}, {"symbol": "TXN", "raw_symbol": "TXN", "description": "TEXAS INSTRUMENTS INC COM USD1.00", "is_option": false, "quantity": 7.068, "last_price": 258.7, "current_value": 1828.49, "cost_basis_total": 1925.0, "average_cost": 272.35, "today_pnl_dollar": -40.01, "today_pnl_pct": -2.15, "total_pnl_dollar": -96.51, "total_pnl_pct": -5.01, "account_type": "Cash", "strategy_tag": "Tactical Momentum", "stop_loss": 240.59, "target_price": 297.5, "entry_date": "Aug 24, 2026", "notes": "", "weight_pct": 0.54}, {"symbol": "INTC", "raw_symbol": "INTC", "description": "INTEL CORP COM USD0.001", "is_option": false, "quantity": 20.0, "last_price": 87.665, "current_value": 1753.3, "cost_basis_total": 1691.8, "average_cost": 84.59, "today_pnl_dollar": -48.1, "today_pnl_pct": -2.68, "total_pnl_dollar": 61.5, "total_pnl_pct": 3.64, "account_type": "Margin", "strategy_tag": "Tactical Momentum", "stop_loss": 81.53, "target_price": 100.81, "entry_date": "Aug 24, 2026", "notes": "", "weight_pct": 0.52}, {"symbol": "DELL", "raw_symbol": "DELL", "description": "DELL TECHNOLOGIES INC CL C", "is_option": false, "quantity": 4.006, "last_price": 436.03, "current_value": 1746.74, "cost_basis_total": 1602.0, "average_cost": 399.9, "today_pnl_dollar": -24.24, "today_pnl_pct": -1.37, "total_pnl_dollar": 144.74, "total_pnl_pct": 9.03, "account_type": "Cash", "strategy_tag": "Tactical Momentum", "stop_loss": 405.51, "target_price": 501.43, "entry_date": "Aug 24, 2026", "notes": "", "weight_pct": 0.52}, {"symbol": "LITE", "raw_symbol": "LITE", "description": "LUMENTUM HLDGS INC COM", "is_option": false, "quantity": 2.0, "last_price": 831.43, "current_value": 1662.86, "cost_basis_total": 1595.2, "average_cost": 797.6, "today_pnl_dollar": -70.56, "today_pnl_pct": -4.08, "total_pnl_dollar": 67.66, "total_pnl_pct": 4.24, "account_type": "Cash", "strategy_tag": "Tactical Momentum", "stop_loss": 773.23, "target_price": 956.14, "entry_date": "Aug 24, 2026", "notes": "", "weight_pct": 0.49}, {"symbol": "DRAM", "raw_symbol": "DRAM", "description": "ROUNDHILL ETF TRUST MEMORY ETF", "is_option": false, "quantity": 30.0, "last_price": 54.575, "current_value": 1637.25, "cost_basis_total": 2050.54, "average_cost": 68.35, "today_pnl_dollar": -93.15, "today_pnl_pct": -5.39, "total_pnl_dollar": -413.29, "total_pnl_pct": -20.16, "account_type": "Cash", "strategy_tag": "Tactical Momentum", "stop_loss": 50.75, "target_price": 62.76, "entry_date": "Aug 24, 2026", "notes": "", "weight_pct": 0.49}, {"symbol": "IEMG", "raw_symbol": "IEMG", "description": "ISHARES CORE MSCI EMERGING MARKETS ETF", "is_option": false, "quantity": 20.156, "last_price": 80.595, "current_value": 1624.47, "cost_basis_total": 1464.32, "average_cost": 72.65, "today_pnl_dollar": -19.66, "today_pnl_pct": -1.2, "total_pnl_dollar": 160.15, "total_pnl_pct": 10.94, "account_type": "Cash", "strategy_tag": "Tactical Momentum", "stop_loss": 74.95, "target_price": 92.68, "entry_date": "Aug 24, 2026", "notes": "", "weight_pct": 0.48}, {"symbol": "FLEX", "raw_symbol": "FLEX", "description": "FLEX LTD COM USD0.01", "is_option": false, "quantity": 15.0, "last_price": 107.22, "current_value": 1608.3, "cost_basis_total": 1861.0, "average_cost": 124.07, "today_pnl_dollar": -48.45, "today_pnl_pct": -2.93, "total_pnl_dollar": -252.7, "total_pnl_pct": -13.58, "account_type": "Cash", "strategy_tag": "Tactical Momentum", "stop_loss": 99.71, "target_price": 123.3, "entry_date": "Aug 24, 2026", "notes": "", "weight_pct": 0.48}, {"symbol": "AGNC", "raw_symbol": "AGNC", "description": "AGNC INVT CORP COM", "is_option": false, "quantity": 146.977, "last_price": 10.925, "current_value": 1605.72, "cost_basis_total": 0.0, "average_cost": 0.0, "today_pnl_dollar": 5.14, "today_pnl_pct": 0.32, "total_pnl_dollar": 1605.72, "total_pnl_pct": 0.0, "account_type": "Cash", "strategy_tag": "Tactical Momentum", "stop_loss": 10.16, "target_price": 12.56, "entry_date": "Aug 24, 2026", "notes": "", "weight_pct": 0.48}, {"symbol": "SKHY", "raw_symbol": "SKHY", "description": "SK HYNIX INC SPON ADS EACH REP 0.1 SHS", "is_option": false, "quantity": 10.0, "last_price": 156.35, "current_value": 1563.5, "cost_basis_total": 1455.8, "average_cost": 145.58, "today_pnl_dollar": -70.6, "today_pnl_pct": -4.33, "total_pnl_dollar": 107.7, "total_pnl_pct": 7.4, "account_type": "Margin", "strategy_tag": "Tactical Momentum", "stop_loss": 145.41, "target_price": 179.8, "entry_date": "Aug 24, 2026", "notes": "", "weight_pct": 0.46}, {"symbol": "MYRG", "raw_symbol": "MYRG", "description": "MYR GRP INC COM USD0.01", "is_option": false, "quantity": 5.0, "last_price": 305.725, "current_value": 1528.62, "cost_basis_total": 2194.1, "average_cost": 438.82, "today_pnl_dollar": -25.73, "today_pnl_pct": -1.66, "total_pnl_dollar": -665.47, "total_pnl_pct": -30.33, "account_type": "Cash", "strategy_tag": "Tactical Momentum", "stop_loss": 284.32, "target_price": 351.58, "entry_date": "Aug 24, 2026", "notes": "", "weight_pct": 0.45}, {"symbol": "SLV", "raw_symbol": "SLV", "description": "ISHARES SILVER TR ISHARES", "is_option": false, "quantity": 24.0, "last_price": 62.15, "current_value": 1491.6, "cost_basis_total": 1527.36, "average_cost": 63.64, "today_pnl_dollar": -13.68, "today_pnl_pct": -0.91, "total_pnl_dollar": -35.76, "total_pnl_pct": -2.34, "account_type": "Cash", "strategy_tag": "Tactical Momentum", "stop_loss": 57.8, "target_price": 71.47, "entry_date": "Aug 24, 2026", "notes": "", "weight_pct": 0.44}, {"symbol": "STRL", "raw_symbol": "STRL", "description": "STERLING INFRASTRUCTURE INC COM", "is_option": false, "quantity": 3.0, "last_price": 491.93, "current_value": 1475.79, "cost_basis_total": 2546.0, "average_cost": 848.67, "today_pnl_dollar": -74.64, "today_pnl_pct": -4.82, "total_pnl_dollar": -1070.21, "total_pnl_pct": -42.03, "account_type": "Cash", "strategy_tag": "Tactical Momentum", "stop_loss": 457.49, "target_price": 565.72, "entry_date": "Aug 24, 2026", "notes": "", "weight_pct": 0.44}, {"symbol": "GLW", "raw_symbol": "GLW", "description": "CORNING INC", "is_option": false, "quantity": 10.035, "last_price": 145.48, "current_value": 1459.89, "cost_basis_total": 1360.0, "average_cost": 135.53, "today_pnl_dollar": -43.76, "today_pnl_pct": -2.91, "total_pnl_dollar": 99.89, "total_pnl_pct": 7.34, "account_type": "Cash", "strategy_tag": "Tactical Momentum", "stop_loss": 135.3, "target_price": 167.3, "entry_date": "Aug 24, 2026", "notes": "", "weight_pct": 0.43}, {"symbol": "CURE", "raw_symbol": "CURE", "description": "DIREXION SHARES ETF TRUST DAILY HEALTHCARE BULL 3X ETF", "is_option": false, "quantity": 10.0, "last_price": 144.41, "current_value": 1444.1, "cost_basis_total": 1185.2, "average_cost": 118.52, "today_pnl_dollar": -2.8, "today_pnl_pct": -0.2, "total_pnl_dollar": 258.9, "total_pnl_pct": 21.84, "account_type": "Cash", "strategy_tag": "Tactical Momentum", "stop_loss": 134.3, "target_price": 166.07, "entry_date": "Aug 24, 2026", "notes": "", "weight_pct": 0.43}, {"symbol": "AVLV", "raw_symbol": "AVLV", "description": "AVANTIS US LARGE CAP VALUE ETF", "is_option": false, "quantity": 15.09, "last_price": 94.55, "current_value": 1426.76, "cost_basis_total": 1253.85, "average_cost": 83.09, "today_pnl_dollar": -1.36, "today_pnl_pct": -0.1, "total_pnl_dollar": 172.91, "total_pnl_pct": 13.79, "account_type": "Cash", "strategy_tag": "Tactical Momentum", "stop_loss": 87.93, "target_price": 108.73, "entry_date": "Aug 24, 2026", "notes": "", "weight_pct": 0.42}, {"symbol": "APLD", "raw_symbol": "APLD", "description": "APPLIED DIGITAL CORP COM USD0.001 (POST REV SPLIT)", "is_option": false, "quantity": 50.0, "last_price": 27.3, "current_value": 1365.0, "cost_basis_total": 1939.5, "average_cost": 38.79, "today_pnl_dollar": 4.5, "today_pnl_pct": 0.33, "total_pnl_dollar": -574.5, "total_pnl_pct": -29.62, "account_type": "Cash", "strategy_tag": "Tactical Momentum", "stop_loss": 25.39, "target_price": 31.39, "entry_date": "Aug 24, 2026", "notes": "", "weight_pct": 0.41}, {"symbol": "NBIS", "raw_symbol": "NBIS", "description": "NEBIUS GROUP N V COM USD0.01 CL A", "is_option": false, "quantity": 6.0, "last_price": 211.24, "current_value": 1267.44, "cost_basis_total": 1257.84, "average_cost": 209.64, "today_pnl_dollar": -47.34, "today_pnl_pct": -3.61, "total_pnl_dollar": 9.6, "total_pnl_pct": 0.76, "account_type": "Cash", "strategy_tag": "Tactical Momentum", "stop_loss": 196.45, "target_price": 242.93, "entry_date": "Aug 24, 2026", "notes": "", "weight_pct": 0.38}, {"symbol": "OIH", "raw_symbol": "OIH", "description": "VANECK ETF TRUST OIL SERVICES ETF", "is_option": false, "quantity": 3.0, "last_price": 405.38, "current_value": 1216.14, "cost_basis_total": 1153.11, "average_cost": 384.37, "today_pnl_dollar": -29.85, "today_pnl_pct": -2.4, "total_pnl_dollar": 63.03, "total_pnl_pct": 5.47, "account_type": "Financing", "strategy_tag": "Tactical Momentum", "stop_loss": 377.0, "target_price": 466.19, "entry_date": "Aug 24, 2026", "notes": "", "weight_pct": 0.36}, {"symbol": "HPE", "raw_symbol": "HPE", "description": "HEWLETT PACKARD ENTERPRISE CO COM", "is_option": false, "quantity": 21.312, "last_price": 52.37, "current_value": 1116.11, "cost_basis_total": 239.99, "average_cost": 11.26, "today_pnl_dollar": -23.02, "today_pnl_pct": -2.03, "total_pnl_dollar": 876.12, "total_pnl_pct": 365.06, "account_type": "Cash", "strategy_tag": "Tactical Momentum", "stop_loss": 48.7, "target_price": 60.23, "entry_date": "Aug 24, 2026", "notes": "", "weight_pct": 0.33}, {"symbol": "GEV", "raw_symbol": "GEV", "description": "GE VERNOVA INC COM", "is_option": false, "quantity": 1.0, "last_price": 940.575, "current_value": 940.58, "cost_basis_total": 958.71, "average_cost": 958.71, "today_pnl_dollar": -16.28, "today_pnl_pct": -1.71, "total_pnl_dollar": -18.13, "total_pnl_pct": -1.89, "account_type": "Cash", "strategy_tag": "Tactical Momentum", "stop_loss": 874.73, "target_price": 1081.66, "entry_date": "Aug 24, 2026", "notes": "", "weight_pct": 0.28}, {"symbol": "AMD", "raw_symbol": "AMD", "description": "ADVANCED MICRO DEVICES INC", "is_option": false, "quantity": 2.0, "last_price": 459.795, "current_value": 919.59, "cost_basis_total": 1036.0, "average_cost": 518.0, "today_pnl_dollar": -26.91, "today_pnl_pct": -2.85, "total_pnl_dollar": -116.41, "total_pnl_pct": -11.24, "account_type": "Margin", "strategy_tag": "Tactical Momentum", "stop_loss": 427.61, "target_price": 528.76, "entry_date": "Aug 24, 2026", "notes": "", "weight_pct": 0.27}, {"symbol": "WDC", "raw_symbol": "WDC", "description": "WESTERN DIGITAL CORP. COM", "is_option": false, "quantity": 2.0, "last_price": 436.41, "current_value": 872.82, "cost_basis_total": 1320.0, "average_cost": 660.0, "today_pnl_dollar": -46.06, "today_pnl_pct": -5.02, "total_pnl_dollar": -447.18, "total_pnl_pct": -33.88, "account_type": "Margin", "strategy_tag": "Tactical Momentum", "stop_loss": 405.86, "target_price": 501.87, "entry_date": "Aug 24, 2026", "notes": "", "weight_pct": 0.26}, {"symbol": "VIAV", "raw_symbol": "VIAV", "description": "VIAVI SOLUTIONS INC COM ISIN #US9255501051 SEDOL #BYSQHH3", "is_option": false, "quantity": 20.0, "last_price": 37.16, "current_value": 743.2, "cost_basis_total": 1052.0, "average_cost": 52.6, "today_pnl_dollar": -34.8, "today_pnl_pct": -4.48, "total_pnl_dollar": -308.8, "total_pnl_pct": -29.35, "account_type": "Cash", "strategy_tag": "Tactical Momentum", "stop_loss": 34.56, "target_price": 42.73, "entry_date": "Aug 24, 2026", "notes": "", "weight_pct": 0.22}, {"symbol": "GLW", "raw_symbol": "GLW", "description": "CORNING INC", "is_option": false, "quantity": 5.0, "last_price": 145.48, "current_value": 727.4, "cost_basis_total": 1055.0, "average_cost": 211.0, "today_pnl_dollar": -21.8, "today_pnl_pct": -2.91, "total_pnl_dollar": -327.6, "total_pnl_pct": -31.05, "account_type": "Margin", "strategy_tag": "Tactical Momentum", "stop_loss": 135.3, "target_price": 167.3, "entry_date": "Aug 24, 2026", "notes": "", "weight_pct": 0.22}, {"symbol": "SPGP", "raw_symbol": "SPGP", "description": "INVESCO EXCHANGE TRADED FD TR S&P 500 GARP ETF", "is_option": false, "quantity": 5.33, "last_price": 128.01, "current_value": 682.29, "cost_basis_total": 445.85, "average_cost": 83.65, "today_pnl_dollar": 3.25, "today_pnl_pct": 0.47, "total_pnl_dollar": 236.44, "total_pnl_pct": 53.03, "account_type": "Cash", "strategy_tag": "Tactical Momentum", "stop_loss": 119.05, "target_price": 147.21, "entry_date": "Aug 24, 2026", "notes": "", "weight_pct": 0.2}, {"symbol": "VSH", "raw_symbol": "VSH", "description": "VISHAY INTERTECHNOLOGY INC COM USD0.10", "is_option": false, "quantity": 20.036, "last_price": 30.35, "current_value": 608.09, "cost_basis_total": 1140.0, "average_cost": 56.9, "today_pnl_dollar": -25.65, "today_pnl_pct": -4.05, "total_pnl_dollar": -531.91, "total_pnl_pct": -46.66, "account_type": "Cash", "strategy_tag": "Tactical Momentum", "stop_loss": 28.23, "target_price": 34.9, "entry_date": "Aug 24, 2026", "notes": "", "weight_pct": 0.18}, {"symbol": "AMAT", "raw_symbol": "AMAT", "description": "APPLIED MATERIALS INC COM USD0.01", "is_option": false, "quantity": 1.0, "last_price": 482.96, "current_value": 482.96, "cost_basis_total": 607.0, "average_cost": 607.0, "today_pnl_dollar": -9.36, "today_pnl_pct": -1.91, "total_pnl_dollar": -124.04, "total_pnl_pct": -20.43, "account_type": "Margin", "strategy_tag": "Tactical Momentum", "stop_loss": 449.15, "target_price": 555.4, "entry_date": "Aug 24, 2026", "notes": "", "weight_pct": 0.14}, {"symbol": "ARM", "raw_symbol": "ARM", "description": "ARM HOLDINGS PLC SPON ADS EACH REP 1 ORD SHS", "is_option": false, "quantity": 2.0, "last_price": 238.82, "current_value": 477.64, "cost_basis_total": 602.6, "average_cost": 301.3, "today_pnl_dollar": -9.0, "today_pnl_pct": -1.85, "total_pnl_dollar": -124.96, "total_pnl_pct": -20.74, "account_type": "Cash", "strategy_tag": "Tactical Momentum", "stop_loss": 222.1, "target_price": 274.64, "entry_date": "Aug 24, 2026", "notes": "", "weight_pct": 0.14}, {"symbol": "TSEM", "raw_symbol": "TSEM", "description": "TOWER SEMICONDUCTOR LTD ORD ILS1", "is_option": false, "quantity": 2.0, "last_price": 214.47, "current_value": 428.94, "cost_basis_total": 507.9, "average_cost": 253.95, "today_pnl_dollar": -16.24, "today_pnl_pct": -3.65, "total_pnl_dollar": -78.96, "total_pnl_pct": -15.55, "account_type": "Cash", "strategy_tag": "Tactical Momentum", "stop_loss": 199.46, "target_price": 246.64, "entry_date": "Aug 24, 2026", "notes": "", "weight_pct": 0.13}, {"symbol": "SIG", "raw_symbol": "SIG", "description": "SIGNET JEWELERS LIMITED SHS", "is_option": false, "quantity": 1.096, "last_price": 83.45, "current_value": 91.46, "cost_basis_total": 67.99, "average_cost": 62.03, "today_pnl_dollar": 2.27, "today_pnl_pct": 2.55, "total_pnl_dollar": 23.47, "total_pnl_pct": 34.52, "account_type": "Cash", "strategy_tag": "Tactical Momentum", "stop_loss": 77.61, "target_price": 95.97, "entry_date": "Aug 24, 2026", "notes": "", "weight_pct": 0.03}, {"symbol": "PLTR261016P125", "raw_symbol": "-PLTR261016P125", "description": "PLTR OCT 16 2026 $125 PUT", "is_option": true, "quantity": 1.0, "last_price": 0.83, "current_value": 83.0, "cost_basis_total": 235.66, "average_cost": 2.36, "today_pnl_dollar": -3.0, "today_pnl_pct": -3.49, "total_pnl_dollar": -152.66, "total_pnl_pct": -64.78, "account_type": "Margin", "strategy_tag": "Options Hedge / Income", "stop_loss": 0.0, "target_price": 0.0, "entry_date": "Aug 24, 2026", "notes": "", "weight_pct": 0.02}, {"symbol": "ZIM", "raw_symbol": "ZIM", "description": "ZIM INTEGRATED SHIPPING SERVCES LTD COM NPV", "is_option": false, "quantity": 2.878, "last_price": 28.6075, "current_value": 82.33, "cost_basis_total": 0.0, "average_cost": 0.0, "today_pnl_dollar": 1.02, "today_pnl_pct": 1.26, "total_pnl_dollar": 82.33, "total_pnl_pct": 0.0, "account_type": "Cash", "strategy_tag": "Tactical Momentum", "stop_loss": 26.6, "target_price": 32.9, "entry_date": "Aug 24, 2026", "notes": "", "weight_pct": 0.02}, {"symbol": "TSM", "raw_symbol": "TSM", "description": "TAIWAN SEMICONDUCTOR MANUFACTURING SPON ADS EACH REP 5 ORD TWD10", "is_option": false, "quantity": 0.109, "last_price": 410.01, "current_value": 44.69, "cost_basis_total": 36.05, "average_cost": 330.73, "today_pnl_dollar": -0.98, "today_pnl_pct": -2.14, "total_pnl_dollar": 8.64, "total_pnl_pct": 23.97, "account_type": "Cash", "strategy_tag": "Tactical Momentum", "stop_loss": 381.31, "target_price": 471.51, "entry_date": "Aug 24, 2026", "notes": "", "weight_pct": 0.01}, {"symbol": "AAPL", "raw_symbol": "AAPL", "description": "APPLE INC", "is_option": false, "quantity": 0.028, "last_price": 312.1841, "current_value": 8.74, "cost_basis_total": 3.67, "average_cost": 131.07, "today_pnl_dollar": 0.07, "today_pnl_pct": 0.91, "total_pnl_dollar": 5.07, "total_pnl_pct": 138.18, "account_type": "Cash", "strategy_tag": "Tactical Momentum", "stop_loss": 290.33, "target_price": 359.01, "entry_date": "Aug 24, 2026", "notes": "", "weight_pct": 0.0}, {"symbol": "VRT", "raw_symbol": "VRT", "description": "VERTIV HOLDINGS CO COM CL A", "is_option": false, "quantity": 0.005, "last_price": 254.14, "current_value": 1.27, "cost_basis_total": 0.64, "average_cost": 128.0, "today_pnl_dollar": -0.04, "today_pnl_pct": -2.99, "total_pnl_dollar": 0.63, "total_pnl_pct": 98.55, "account_type": "Cash", "strategy_tag": "Tactical Momentum", "stop_loss": 236.35, "target_price": 292.26, "entry_date": "Aug 24, 2026", "notes": "", "weight_pct": 0.0}, {"symbol": "VTR", "raw_symbol": "VTR", "description": "VENTAS INC", "is_option": false, "quantity": 0.0001, "last_price": 93.115, "current_value": 0.01, "cost_basis_total": 0.0, "average_cost": 0.0, "today_pnl_dollar": 0.0, "today_pnl_pct": 0.05, "total_pnl_dollar": 0.0, "total_pnl_pct": 0.0, "account_type": "Cash", "strategy_tag": "Tactical Momentum", "stop_loss": 86.6, "target_price": 107.08, "entry_date": "Aug 24, 2026", "notes": "", "weight_pct": 0.0}, {"symbol": "PLTR261016P135", "raw_symbol": "-PLTR261016P135", "description": "PLTR OCT 16 2026 $135 PUT", "is_option": true, "quantity": -1.0, "last_price": 1.44, "current_value": -144.0, "cost_basis_total": 419.34, "average_cost": 4.19, "today_pnl_dollar": -9.0, "today_pnl_pct": -6.67, "total_pnl_dollar": -563.34, "total_pnl_pct": -134.34, "account_type": "Margin", "strategy_tag": "Options Hedge / Income", "stop_loss": 0.0, "target_price": 0.0, "entry_date": "Aug 24, 2026", "notes": "", "weight_pct": -0.04}, {"symbol": "PLTR261016C190", "raw_symbol": "-PLTR261016C190", "description": "PLTR OCT 16 2026 $190 CALL", "is_option": true, "quantity": -1.0, "last_price": 8.45, "current_value": -845.0, "cost_basis_total": 706.32, "average_cost": 7.06, "today_pnl_dollar": 131.0, "today_pnl_pct": 13.42, "total_pnl_dollar": -1551.32, "total_pnl_pct": -219.63, "account_type": "Cash", "strategy_tag": "Options Hedge / Income", "stop_loss": 0.0, "target_price": 0.0, "entry_date": "Aug 24, 2026", "notes": "", "weight_pct": -0.25}], "total_day_pnl_dollar": -5125.13, "total_day_pnl_pct": -1.5, "total_unrealized_pnl_dollar": 44982.46, "cash_weight_pct": 21.03};

    document.addEventListener('DOMContentLoaded', () => {
        // Check if user has saved portfolio in localStorage
        try {
            const localSaved = localStorage.getItem('user_portfolio_data');
            if (localSaved) {
                const parsed = JSON.parse(localSaved);
                if (parsed && parsed.positions && parsed.positions.length > 0) {
                    window.portfolioData = parsed;
                }
            }
        } catch (e) {
            console.error('Could not load localStorage portfolio:', e);
        }

        initTableState('day-table');
        initTableState('eco-table');
        initTableState('earn-table');
        initTableState('analyst-table');
        initTableState('options-table');
        
        renderPortfolioDOM();

        loadFilterPreferences();
        filterDayWatchlist(false);
    });

    function switchMainView(view) {
        const btnScreener = document.getElementById('nav-tab-screener');
        const btnPortfolio = document.getElementById('nav-tab-portfolio');
        const btnMacro = document.getElementById('nav-tab-macro');
        
        const secScreener = document.getElementById('view-screener-section');
        const secPortfolio = document.getElementById('view-portfolio-section');
        const secMacro = document.getElementById('view-macro-section');

        if (btnScreener) btnScreener.classList.remove('active');
        if (btnPortfolio) btnPortfolio.classList.remove('active');
        if (btnMacro) btnMacro.classList.remove('active');

        if (view === 'screener') {
            if (btnScreener) btnScreener.classList.add('active');
            if (secScreener) secScreener.style.display = 'block';
            if (secMacro) secMacro.style.display = 'block';
            if (secPortfolio) secPortfolio.style.display = 'none';
        } else if (view === 'portfolio') {
            if (btnPortfolio) btnPortfolio.classList.add('active');
            if (secPortfolio) secPortfolio.style.display = 'block';
            if (secScreener) secScreener.style.display = 'none';
            if (secMacro) secMacro.style.display = 'none';
        } else if (view === 'macro') {
            if (btnMacro) btnMacro.classList.add('active');
            if (secMacro) secMacro.style.display = 'block';
            if (secScreener) secScreener.style.display = 'none';
            if (secPortfolio) secPortfolio.style.display = 'none';
        }
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    function openModal(id) {
        const m = document.getElementById(id);
        if (m) m.style.display = 'flex';
    }

    function closeModal(id) {
        const m = document.getElementById(id);
        if (m) m.style.display = 'none';
    }

    /* Dynamic Portfolio DOM Builder */
    function renderPortfolioDOM() {
        const pData = window.portfolioData || { positions: [] };
        const nav = pData.total_nav || 0;
        const cash = pData.cash_balance || 0;
        const eq = pData.equity_value || (nav - cash);
        const dayD = pData.total_day_pnl_dollar || 0;
        const dayP = pData.total_day_pnl_pct || (nav > 0 ? (dayD / nav) * 100 : 0);
        const totD = pData.total_unrealized_pnl_dollar || 0;
        const cashW = nav > 0 ? ((cash / nav) * 100).toFixed(1) : '0.0';

        const dayColor = dayD >= 0 ? '#34d399' : '#f87171';
        const totColor = totD >= 0 ? '#34d399' : '#f87171';

        // Update Top Navbar
        const topNav = document.getElementById('top-nav-val');
        if (topNav) topNav.innerText = '$' + nav.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2});
        const topCash = document.getElementById('top-cash-val');
        if (topCash) topCash.innerText = '$' + cash.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2}) + ' (' + cashW + '%)';
        const topPnl = document.getElementById('top-pnl-val');
        if (topPnl) {
            topPnl.style.color = dayColor;
            topPnl.innerText = (dayD >= 0 ? '+$' : '-$') + Math.abs(dayD).toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2}) + ' (' + (dayP >= 0 ? '+' : '') + dayP.toFixed(2) + '%)';
        }

        // Update Portfolio Cards
        const cardNav = document.getElementById('port-card-nav');
        if (cardNav) cardNav.innerText = '$' + nav.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2});
        const cardCash = document.getElementById('port-card-cash');
        if (cardCash) cardCash.innerText = 'Liquid Cash: $' + cash.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2}) + ' (' + cashW + '%)';
        const cardEq = document.getElementById('port-card-eq');
        if (cardEq) cardEq.innerText = '$' + eq.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2});
        const cardCount = document.getElementById('port-card-count');
        if (cardCount) cardCount.innerText = 'Positions: ' + (pData.positions ? pData.positions.length : 0) + ' Assets';
        const cardDayPnl = document.getElementById('port-card-day-pnl');
        if (cardDayPnl) {
            cardDayPnl.style.color = dayColor;
            cardDayPnl.innerText = (dayD >= 0 ? '+$' : '-$') + Math.abs(dayD).toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2});
        }
        const cardDayPct = document.getElementById('port-card-day-pct');
        if (cardDayPct) {
            cardDayPct.style.color = dayColor;
            cardDayPct.innerText = (dayP >= 0 ? '+' : '') + dayP.toFixed(2) + '% Return';
        }
        const cardTotPnl = document.getElementById('port-card-tot-pnl');
        if (cardTotPnl) {
            cardTotPnl.style.color = totColor;
            cardTotPnl.innerText = (totD >= 0 ? '+$' : '-$') + Math.abs(totD).toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2});
        }

        // Populate Table Rows
        const tbody = document.querySelector('#portfolio-table tbody');
        if (!tbody) return;
        tbody.innerHTML = '';

        const positions = pData.positions || [];
        if (positions.length === 0) {
            tbody.innerHTML = '<tr><td colspan="13" style="text-align: center; color: #9ca3af; padding: 24px;">No positions found in active book. Click "Import Fidelity CSV" to load positions.</td></tr>';
            return;
        }

        const rowElements = [];
        positions.forEach(p => {
            const sym = p.symbol || '—';
            const desc = p.description || '—';
            const qty = p.quantity || 0;
            const avgC = p.average_cost || 0;
            const lastP = p.last_price || 0;
            const curV = p.current_value || (qty * lastP);
            const pDayD = p.today_pnl_dollar || 0;
            const pDayP = p.today_pnl_pct || 0;
            const pTotD = p.total_pnl_dollar || 0;
            const pTotP = p.total_pnl_pct || 0;
            const wPct = p.weight_pct || (nav > 0 ? (curV / nav) * 100 : 0);
            const strat = p.strategy_tag || 'Tactical';
            const stopL = p.stop_loss || 0;
            const targP = p.target_price || 0;
            const notes = p.notes || '';
            const isOpt = p.is_option || false;

            const pDayColor = pDayD >= 0 ? '#34d399' : '#f87171';
            const pTotColor = pTotD >= 0 ? '#34d399' : '#f87171';

            const tr = document.createElement('tr');
            tr.className = 'data-row';
            tr.setAttribute('data-symbol', sym);
            tr.setAttribute('data-is-option', isOpt ? 'true' : 'false');
            tr.innerHTML = 
                '<td><strong style="color: #60a5fa;">' + sym + '</strong></td>' +
                '<td style="font-size: 11px; color: #d1d5db; max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">' + desc + '</td>' +
                '<td><strong>' + qty.toLocaleString('en-US', {minimumFractionDigits: 0, maximumFractionDigits: 3}) + '</strong></td>' +
                '<td>$' + avgC.toFixed(2) + '</td>' +
                '<td><strong>$' + lastP.toFixed(2) + '</strong></td>' +
                '<td style="color: ' + pDayColor + '; font-weight: 600;">' + (pDayD >= 0 ? '+' : '') + pDayD.toFixed(2) + '</td>' +
                '<td style="color: ' + pDayColor + '; font-weight: 600;">' + (pDayP >= 0 ? '+' : '') + pDayP.toFixed(2) + '%</td>' +
                '<td style="color: ' + pTotColor + '; font-weight: 700;">' + (pTotD >= 0 ? '+' : '') + pTotD.toFixed(2) + '</td>' +
                '<td style="color: ' + pTotColor + '; font-weight: 700;">' + (pTotP >= 0 ? '+' : '') + pTotP.toFixed(2) + '%</td>' +
                '<td><strong>$' + curV.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2}) + '</strong></td>' +
                '<td><span class="pill pill-blue">' + wPct.toFixed(2) + '%</span></td>' +
                '<td><span class="pill pill-purple">' + strat + '</span></td>' +
                '<td style="text-align: center; white-space: nowrap;">' +
                    '<button class="btn-action" style="padding: 2px 6px; font-size: 10px;" onclick="openSizingModal('' + sym + '', ' + lastP + ', ' + stopL + ', '' + desc.replace(/'/g, '') + '', 'Rebalance')">⚡</button>' +
                    '<button class="btn-secondary" style="padding: 2px 6px; font-size: 10px;" onclick="openEditPositionModal('' + sym + '', ' + qty + ', ' + avgC + ', ' + stopL + ', ' + targP + ', '' + strat + '', '' + notes.replace(/'/g, '') + '')">✏️</button>' +
                    '<button class="btn-danger" style="padding: 2px 6px; font-size: 10px;" onclick="deletePortfolioPosition('' + sym + '')">❌</button>' +
                '</td>';
            tbody.appendChild(tr);
            rowElements.push(tr);
        });

        tableStates['portfolio-table'].allRows = rowElements;
        tableStates['portfolio-table'].filteredRows = [...rowElements];
        renderTablePage('portfolio-table');
    }

    /* Sizing Modal Calculations */
    function openSizingModal(ticker, price, stop, desc, posType) {
        document.getElementById('sizing-ticker').value = ticker;
        document.getElementById('sizing-price').value = price || 100.0;
        document.getElementById('sizing-stop').value = stop || (price * 0.96);
        recalcSizing();
        openModal('modal-sizing');
    }

    function recalcSizing() {
        const nav = parseFloat(document.getElementById('sizing-nav').value) || (window.portfolioData ? window.portfolioData.total_nav : 336870.83);
        const riskPct = parseFloat(document.getElementById('sizing-risk-pct').value) || 0.75;
        const price = parseFloat(document.getElementById('sizing-price').value) || 100.0;
        const stop = parseFloat(document.getElementById('sizing-stop').value) || (price * 0.96);
        const macroMult = 0.95 || 0.95;
        const flowFactor = 1.00;

        const riskDollar = nav * (riskPct / 100.0);
        const stopDistDollar = Math.max(price * 0.015, Math.abs(price - stop));
        const stopDistPct = (stopDistDollar / price) * 100.0;
        const baseShares = riskDollar / stopDistDollar;
        const effectiveMult = macroMult * flowFactor;
        const finalShares = Math.max(1, Math.floor(baseShares * effectiveMult));
        const totalCapital = finalShares * price;
        const weightPct = (totalCapital / nav) * 100.0;

        document.getElementById('calc-stop-dist').innerText = stopDistPct.toFixed(2) + '%';
        document.getElementById('calc-risk-dollar').innerText = '$' + riskDollar.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2});
        document.getElementById('calc-shares').innerText = finalShares.toLocaleString() + ' Shares';
        document.getElementById('calc-total-capital').innerText = '$' + totalCapital.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2});
        document.getElementById('calc-nav-weight').innerText = weightPct.toFixed(2) + '%';
    }

    function addSizingToPortfolio() {
        const ticker = document.getElementById('sizing-ticker').value.toUpperCase();
        const price = parseFloat(document.getElementById('sizing-price').value);
        const stop = parseFloat(document.getElementById('sizing-stop').value);
        const sharesText = document.getElementById('calc-shares').innerText;
        const shares = parseInt(sharesText.replace(/[^0-9]/g, ''), 10) || 10;

        if (!window.portfolioData) window.portfolioData = { positions: [], total_nav: 336870.83, cash_balance: 70830.35 };
        const pos = window.portfolioData.positions || [];
        const existingIdx = pos.findIndex(p => p.symbol === ticker);

        const newPos = {
            symbol: ticker,
            description: ticker + ' Equity Position',
            is_option: false,
            quantity: shares,
            last_price: price,
            current_value: shares * price,
            cost_basis_total: shares * price,
            average_cost: price,
            today_pnl_dollar: 0.0,
            today_pnl_pct: 0.0,
            total_pnl_dollar: 0.0,
            total_pnl_pct: 0.0,
            strategy_tag: 'Tactical Momentum',
            stop_loss: stop,
            target_price: +(price * 1.15).toFixed(2),
            entry_date: 'Aug 24, 2026',
            notes: 'Added from Sizing Calculator'
        };

        if (existingIdx >= 0) {
            pos[existingIdx] = Object.assign(pos[existingIdx], newPos);
        } else {
            pos.unshift(newPos);
        }

        recomputePortfolioMetrics();
        alert('Added ' + shares + ' shares of ' + ticker + ' at $' + price.toFixed(2) + ' to Active Portfolio.');
        closeModal('modal-sizing');
    }

    function openFidelityImportModal() {
        openModal('modal-import-fidelity');
    }

    function handleFidelityFileUpload(input) {
        const file = input.files[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = (e) => {
            document.getElementById('fidelity-csv-text').value = e.target.result;
        };
        reader.readAsText(file);
    }

    /* Robust Client-Side Fidelity CSV Parser */
    function parseCSVLine(line) {
        const result = [];
        let cur = '';
        let inQuotes = false;
        for (let i = 0; i < line.length; i++) {
            const c = line[i];
            if (c === '"') {
                inQuotes = !inQuotes;
            } else if (c === ',' && !inQuotes) {
                result.push(cur.trim());
                cur = '';
            } else {
                cur += c;
            }
        }
        result.push(cur.trim());
        return result;
    }

    function cleanNum(val) {
        if (!val) return 0.0;
        const clean = String(val).replace(/[$,%]/g, '').trim();
        if (clean === '--' || clean === '—' || clean === 'N/A' || clean === '') return 0.0;
        const num = parseFloat(clean);
        return isNaN(num) ? 0.0 : num;
    }

    function processFidelityImport() {
        const rawText = document.getElementById('fidelity-csv-text').value.trim();
        if (!rawText) {
            alert('Please paste or upload Fidelity CSV content first.');
            return;
        }

        const rawLines = rawText.split(String.fromCharCode(10));
        const lines = [];
        for (let i = 0; i < rawLines.length; i++) {
            const l = rawLines[i].replace(String.fromCharCode(13), '').trim();
            if (l.length > 0) lines.push(l);
        }

        let headerIdx = -1;
        for (let i = 0; i < lines.length; i++) {
            if (lines[i].indexOf('Account number') >= 0 && lines[i].indexOf('Symbol') >= 0) {
                headerIdx = i;
                break;
            }
        }

        if (headerIdx === -1) {
            alert('Could not find Fidelity CSV header row (must contain "Account number" and "Symbol"). Please verify your export.');
            return;
        }

        const headers = parseCSVLine(lines[headerIdx]);
        const getIdx = function(name) {
            return headers.findIndex(function(h) { return h.toLowerCase().indexOf(name.toLowerCase()) >= 0; });
        };

        const symIdx = getIdx('Symbol');
        const descIdx = getIdx('Description');
        const qtyIdx = getIdx('Quantity');
        const lastPIdx = getIdx('Last price');
        const curVIdx = getIdx('Current value');
        const costTotIdx = getIdx('Cost basis total');
        const avgCostIdx = getIdx('Average cost');
        const dayDIdx = getIdx("Today's gain/loss dollar");
        const dayPIdx = getIdx("Today's gain/loss percent");
        const totDIdx = getIdx("Total gain/loss dollar");
        const totPIdx = getIdx("Total gain/loss percent");
        const accNumIdx = getIdx('Account number');
        const accNmIdx = getIdx('Account name');
        const typeIdx = getIdx('Type');

        let cashBalance = 0.0;
        let positions = [];
        let accNumber = '';
        let accName = '';

        for (let i = headerIdx + 1; i < lines.length; i++) {
            const cols = parseCSVLine(lines[i]);
            if (cols.length < 3) continue;

            const symRaw = (cols[symIdx] || '').trim();
            const desc = (cols[descIdx] || '').trim();
            const accNum = (cols[accNumIdx] || '').trim();
            const accNm = (cols[accNmIdx] || '').trim();

            if (accNum && !accNumber) accNumber = accNum;
            if (accNm && !accName) accName = accNm;

            // Check for cash line
            if (symRaw.indexOf('SPAXX') >= 0 || desc.toUpperCase().indexOf('MONEY MARKET') >= 0 || accNm.indexOf('Pending activity') >= 0 || desc.indexOf('Pending activity') >= 0) {
                let val = cleanNum(cols[curVIdx]);
                if (val === 0) {
                    for (let j = 0; j < cols.length; j++) {
                        let cand = cleanNum(cols[j]);
                        if (cand > 0) { val = cand; break; }
                    }
                }
                cashBalance += val;
                continue;
            }

            // Skip disclaimers & empty lines
            if (!symRaw || symRaw.indexOf('The data and information') >= 0 || symRaw.indexOf('Brokerage services') >= 0 || symRaw.indexOf('Date downloaded') >= 0) {
                continue;
            }

            const qty = cleanNum(cols[qtyIdx]);
            if (qty === 0 && !symRaw.startsWith('-')) continue;

            const lastP = cleanNum(cols[lastPIdx]);
            const curV = cleanNum(cols[curVIdx]);
            const dayD = cleanNum(cols[dayDIdx]);
            const dayP = cleanNum(cols[dayPIdx]);
            const totD = cleanNum(cols[totDIdx]);
            const totP = cleanNum(cols[totPIdx]);
            const costTot = cleanNum(cols[costTotIdx]);
            const avgC = cleanNum(cols[avgCostIdx]) || (qty > 0 ? (costTot / qty) : lastP);
            const posType = (cols[typeIdx] || 'Cash').trim();

            const isOption = symRaw.startsWith('-') || desc.toUpperCase().indexOf('CALL') >= 0 || desc.toUpperCase().indexOf('PUT') >= 0;
            const cleanSym = symRaw.replace('-', '').replace(' ', '');

            let strat = 'Tactical Momentum';
            if (isOption) strat = 'Options Hedge / Income';
            else if (qty > 50 && curV > 10000) strat = 'Core Long Holding';

            positions.push({
                symbol: isOption ? cleanSym : symRaw,
                raw_symbol: symRaw,
                description: desc,
                is_option: isOption,
                quantity: qty,
                last_price: lastP,
                current_value: curV,
                cost_basis_total: costTot,
                average_cost: avgC,
                today_pnl_dollar: dayD,
                today_pnl_pct: dayP,
                total_pnl_dollar: totD,
                total_pnl_pct: totP,
                account_type: posType,
                strategy_tag: strat,
                stop_loss: !isOption ? +(lastP * 0.93).toFixed(2) : 0,
                target_price: !isOption ? +(lastP * 1.15).toFixed(2) : 0,
                entry_date: 'Aug 24, 2026',
                notes: ''
            });
        }

        const totalEquity = positions.reduce(function(acc, p) { return acc + p.current_value; }, 0);
        const totalNav = cashBalance + totalEquity;

        positions.forEach(function(p) {
            p.weight_pct = totalNav > 0 ? +((p.current_value / totalNav) * 100).toFixed(2) : 0.0;
        });

        window.portfolioData = {
            account_number: accNumber || '264695485',
            account_name: accName || 'Traditional IRA',
            last_updated: new Date().toLocaleString(),
            total_nav: +totalNav.toFixed(2),
            cash_balance: +cashBalance.toFixed(2),
            equity_value: +totalEquity.toFixed(2),
            risk_budget_pct: 0.75,
            positions_count: positions.length,
            positions: positions,
            total_day_pnl_dollar: +positions.reduce(function(acc, p) { return acc + p.today_pnl_dollar; }, 0).toFixed(2),
            total_day_pnl_pct: totalNav > 0 ? +(positions.reduce(function(acc, p) { return acc + p.today_pnl_dollar; }, 0) / totalNav * 100).toFixed(2) : 0.0,
            total_unrealized_pnl_dollar: +positions.reduce(function(acc, p) { return acc + p.total_pnl_dollar; }, 0).toFixed(2),
            cash_weight_pct: totalNav > 0 ? +((cashBalance / totalNav) * 100).toFixed(2) : 0.0
        };

        try {
            localStorage.setItem('user_portfolio_data', JSON.stringify(window.portfolioData));
        } catch (e) {
            console.error('Could not save to localStorage:', e);
        }

        renderPortfolioDOM();
        closeModal('modal-import-fidelity');

        const msg = [
            'Successfully imported ' + positions.length + ' positions from Fidelity!',
            'Total Account NAV: $' + totalNav.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2}),
            'Liquid Cash (SPAXX): $' + cashBalance.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2}),
            'Open Equities & Options: $' + totalEquity.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})
        ].join(String.fromCharCode(10));
        alert(msg);
    }

    function recomputePortfolioMetrics() {
        if (!window.portfolioData) return;
        const pData = window.portfolioData;
        const pos = pData.positions || [];
        const cash = pData.cash_balance || 0;
        const totalEq = pos.reduce((acc, p) => acc + (p.current_value || (p.quantity * p.last_price)), 0);
        const totalNav = cash + totalEq;
        pos.forEach(p => {
            p.weight_pct = totalNav > 0 ? +((p.current_value / totalNav) * 100).toFixed(2) : 0.0;
        });
        pData.total_nav = +totalNav.toFixed(2);
        pData.equity_value = +totalEq.toFixed(2);
        pData.positions_count = pos.length;
        pData.total_day_pnl_dollar = +pos.reduce((acc, p) => acc + (p.today_pnl_dollar || 0), 0).toFixed(2);
        pData.total_day_pnl_pct = totalNav > 0 ? +(pData.total_day_pnl_dollar / totalNav * 100).toFixed(2) : 0.0;
        pData.total_unrealized_pnl_dollar = +pos.reduce((acc, p) => acc + (p.total_pnl_dollar || 0), 0).toFixed(2);
        pData.cash_weight_pct = totalNav > 0 ? +((cash / totalNav) * 100).toFixed(2) : 0.0;

        try {
            localStorage.setItem('user_portfolio_data', JSON.stringify(pData));
        } catch (e) {}

        renderPortfolioDOM();
    }

    function openEditPositionModal(sym, qty, avgCost, stop, target, strat, notes) {
        document.getElementById('edit-pos-symbol').value = sym;
        document.getElementById('edit-pos-qty').value = qty;
        document.getElementById('edit-pos-avg-cost').value = avgCost;
        document.getElementById('edit-pos-stop').value = stop || (avgCost * 0.94).toFixed(2);
        document.getElementById('edit-pos-target').value = target || (avgCost * 1.15).toFixed(2);
        document.getElementById('edit-pos-strategy').value = strat || 'Core Long Holding';
        document.getElementById('edit-pos-notes').value = notes || '';
        openModal('modal-edit-position');
    }

    function savePositionEdit() {
        const sym = document.getElementById('edit-pos-symbol').value;
        const qty = parseFloat(document.getElementById('edit-pos-qty').value);
        const avgCost = parseFloat(document.getElementById('edit-pos-avg-cost').value);
        const stop = parseFloat(document.getElementById('edit-pos-stop').value);
        const target = parseFloat(document.getElementById('edit-pos-target').value);
        const strat = document.getElementById('edit-pos-strategy').value;
        const notes = document.getElementById('edit-pos-notes').value;

        if (window.portfolioData && window.portfolioData.positions) {
            const pos = window.portfolioData.positions.find(p => p.symbol === sym);
            if (pos) {
                pos.quantity = qty;
                pos.average_cost = avgCost;
                pos.stop_loss = stop;
                pos.target_price = target;
                pos.strategy_tag = strat;
                pos.notes = notes;
                pos.current_value = +(qty * pos.last_price).toFixed(2);
                recomputePortfolioMetrics();
            }
        }

        alert('Saved changes for position ' + sym);
        closeModal('modal-edit-position');
    }

    function deletePortfolioPosition(sym) {
        if (confirm('Are you sure you want to remove ' + sym + ' from your portfolio book?')) {
            if (window.portfolioData && window.portfolioData.positions) {
                window.portfolioData.positions = window.portfolioData.positions.filter(p => p.symbol !== sym);
                recomputePortfolioMetrics();
            }
            alert('Position ' + sym + ' deleted.');
        }
    }

    function exportPortfolioJSON() {
        const jsonStr = JSON.stringify(window.portfolioData || {}, null, 2);
        const blob = new Blob([jsonStr], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'portfolio.json';
        a.click();
    }

    function filterPortfolioType(type) {
        const table = document.getElementById('portfolio-table');
        const rows = table.querySelectorAll('tbody tr.data-row');
        rows.forEach(r => {
            const isOpt = r.getAttribute('data-is-option') === 'true';
            if (type === 'ALL') r.style.display = '';
            else if (type === 'STOCK') r.style.display = isOpt ? 'none' : '';
            else if (type === 'OPTION') r.style.display = isOpt ? '' : 'none';
        });
    }

    function filterPortfolioTable(q) {
        const query = (q || '').toLowerCase().trim();
        const table = document.getElementById('portfolio-table');
        const rows = table.querySelectorAll('tbody tr.data-row');
        rows.forEach(r => {
            const text = r.innerText.toLowerCase();
            r.style.display = text.includes(query) ? '' : 'none';
        });
    }

    /* Core Table Sorting & Filtering */
    function initTableState(tableId) {
        const table = document.getElementById(tableId);
        if (!table) return;
        const rows = Array.from(table.querySelectorAll('tbody tr.data-row'));
        tableStates[tableId].allRows = rows;
        tableStates[tableId].filteredRows = [...rows];
        renderTablePage(tableId);
    }

    function renderTablePage(tableId) {
        const state = tableStates[tableId];
        if (!state) return;
        const table = document.getElementById(tableId);
        const tbody = table.querySelector('tbody');
        const start = (state.currentPage - 1) * state.pageSize;
        const end = start + state.pageSize;

        const allDrawerMap = new Map();
        table.querySelectorAll('tbody tr.row-drawer, tbody tr.whale-drawer').forEach(d => {
            allDrawerMap.set(d.id, d);
        });

        tbody.innerHTML = '';
        const pageRows = state.filteredRows.slice(start, end);

        if (pageRows.length === 0) {
            const colCount = table.querySelectorAll('thead th').length || 15;
            tbody.innerHTML = `<tr><td colspan="${colCount}" style="text-align: center; color: #9ca3af; padding: 24px;">No matching records found.</td></tr>`;
        } else {
            pageRows.forEach(r => {
                tbody.appendChild(r);
                const drawerId = r.getAttribute('data-drawer-id') || r.getAttribute('data-whale-id');
                if (drawerId && allDrawerMap.has(drawerId)) {
                    tbody.appendChild(allDrawerMap.get(drawerId));
                }
            });
        }

        renderPaginationControls(tableId);
    }

    function renderPaginationControls(tableId) {
        const state = tableStates[tableId];
        const container = document.getElementById(`${tableId}-pagination`);
        if (!container) return;

        const totalItems = state.filteredRows.length;
        const totalPages = Math.ceil(totalItems / state.pageSize) || 1;
        const startItem = totalItems > 0 ? (state.currentPage - 1) * state.pageSize + 1 : 0;
        const endItem = Math.min(state.currentPage * state.pageSize, totalItems);

        let html = `<div>Showing ${startItem} to ${endItem} of ${totalItems} entries</div>`;
        html += `<div class="page-btns">`;
        html += `<button class="page-btn" ${state.currentPage === 1 ? 'disabled' : ''} onclick="changePage('${tableId}', 1)">&laquo;</button>`;
        html += `<button class="page-btn" ${state.currentPage === 1 ? 'disabled' : ''} onclick="changePage('${tableId}', ${state.currentPage - 1})">&lsaquo;</button>`;

        const maxButtons = 5;
        let startPage = Math.max(1, state.currentPage - Math.floor(maxButtons / 2));
        let endPage = Math.min(totalPages, startPage + maxButtons - 1);
        if (endPage - startPage + 1 < maxButtons) {
            startPage = Math.max(1, endPage - maxButtons + 1);
        }

        for (let i = startPage; i <= endPage; i++) {
            html += `<button class="page-btn ${i === state.currentPage ? 'active' : ''}" onclick="changePage('${tableId}', ${i})">${i}</button>`;
        }

        html += `<button class="page-btn" ${state.currentPage === totalPages ? 'disabled' : ''} onclick="changePage('${tableId}', ${state.currentPage + 1})">&rsaquo;</button>`;
        html += `<button class="page-btn" ${state.currentPage === totalPages ? 'disabled' : ''} onclick="changePage('${tableId}', ${totalPages})">&raquo;</button>`;
        html += `</div>`;

        container.innerHTML = html;
    }

    function changePage(tableId, page) {
        const state = tableStates[tableId];
        if (!state) return;
        const totalPages = Math.ceil(state.filteredRows.length / state.pageSize) || 1;
        state.currentPage = Math.max(1, Math.min(page, totalPages));
        renderTablePage(tableId);
    }

    function changePageSize(tableId, size) {
        const state = tableStates[tableId];
        if (!state) return;
        state.pageSize = parseInt(size, 10);
        state.currentPage = 1;
        renderTablePage(tableId);
    }

    function toggleRowDrawer(drawerId) {
        const drawer = document.getElementById(drawerId);
        if (drawer) {
            drawer.style.display = drawer.style.display === 'table-row' ? 'none' : 'table-row';
        }
    }

    function toggleWhaleDrawer(drawerId) {
        const drawer = document.getElementById(drawerId);
        if (drawer) {
            drawer.style.display = drawer.style.display === 'table-row' ? 'none' : 'table-row';
        }
    }

    function switchWatchlistView(mode, save = true) {
        const table = document.getElementById('day-table');
        if (!table) return;

        table.classList.remove('view-core', 'view-technical', 'view-options');
        table.classList.add(`view-${mode}`);

        document.getElementById('btn-view-core').classList.toggle('active', mode === 'core');
        document.getElementById('btn-view-technical').classList.toggle('active', mode === 'technical');
        document.getElementById('btn-view-options').classList.toggle('active', mode === 'options');

        window.currentWatchlistView = mode;
        if (save) saveFilterPreferences();
    }

    function switchEarningsTab(filterVal) {
        document.querySelectorAll('.tab-bar .tab-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        event.target.classList.add('active');

        const state = tableStates['earn-table'];
        if (!state) return;

        if (filterVal === 'all') {
            state.filteredRows = [...state.allRows];
        } else {
            state.filteredRows = state.allRows.filter(r => {
                const text = r.innerText.toLowerCase();
                return text.includes(filterVal.toLowerCase());
            });
        }
        state.currentPage = 1;
        renderTablePage('earn-table');
    }

    function filterEconomicImpact() {
        const showHigh = document.getElementById('filter-high').checked;
        const showMed = document.getElementById('filter-med').checked;
        const showLow = document.getElementById('filter-low').checked;

        const state = tableStates['eco-table'];
        if (!state) return;

        state.filteredRows = state.allRows.filter(r => {
            const impactCell = r.children[1] ? r.children[1].innerText.trim() : '';
            if (impactCell === 'HIGH' && !showHigh) return false;
            if (impactCell === 'MED' && !showMed) return false;
            if (impactCell === 'LOW' && !showLow) return false;
            return true;
        });

        state.currentPage = 1;
        renderTablePage('eco-table');
    }

    function sortTable(tableId, colIdx) {
        const state = tableStates[tableId];
        if (!state) return;
        const table = document.getElementById(tableId);
        const th = table.querySelectorAll('thead th')[colIdx];
        if (!th) return;

        const isAsc = th.classList.contains('asc');
        table.querySelectorAll('thead th').forEach(h => {
            h.classList.remove('asc', 'desc');
            const icon = h.querySelector('.sort-icon');
            if (icon) icon.innerText = '';
        });

        th.classList.add(isAsc ? 'desc' : 'asc');
        const icon = th.querySelector('.sort-icon');
        if (icon) icon.innerText = isAsc ? ' ▼' : ' ▲';

        state.filteredRows.sort((a, b) => {
            const valA = (a.children[colIdx] ? a.children[colIdx].innerText.trim() : '').replace(/[$,%x★]/g, '');
            const valB = (b.children[colIdx] ? b.children[colIdx].innerText.trim() : '').replace(/[$,%x★]/g, '');

            const numA = parseFloat(valA);
            const numB = parseFloat(valB);

            if (!isNaN(numA) && !isNaN(numB)) {
                return isAsc ? numB - numA : numA - numB;
            }
            return isAsc ? valB.localeCompare(valA) : valA.localeCompare(valB);
        });

        renderTablePage(tableId);
    }

    function filterTable(tableId, query) {
        const state = tableStates[tableId];
        if (!state) return;
        const q = (query || '').toLowerCase().trim();
        state.filteredRows = state.allRows.filter(r => {
            return r.innerText.toLowerCase().includes(q);
        });
        state.currentPage = 1;
        renderTablePage(tableId);
    }

    /* Watchlist Multi-Factor Interactive Filter with LocalStorage Persistence */
    function saveFilterPreferences() {
        try {
            const prefs = {
                reqLastHigh: document.getElementById('filter-breakout-last').checked,
                reqPmHigh: document.getElementById('filter-breakout-pm').checked,
                filterChg: document.getElementById('filter-chg') ? document.getElementById('filter-chg').value : 'ALL',
                minGap: document.getElementById('filter-gap') ? document.getElementById('filter-gap').value : '3.0',
                filterOpen: document.getElementById('filter-open') ? document.getElementById('filter-open').value : 'ALL',
                filterVwap: document.getElementById('filter-vwap') ? document.getElementById('filter-vwap').value : 'ALL',
                filterFlow: document.getElementById('filter-flow') ? document.getElementById('filter-flow').value : 'ALL',
                filterSma20: document.getElementById('filter-sma20') ? document.getElementById('filter-sma20').value : 'ALL',
                filterSma50: document.getElementById('filter-sma50') ? document.getElementById('filter-sma50').value : 'ALL',
                filterSma200: document.getElementById('filter-sma200') ? document.getElementById('filter-sma200').value : 'ALL',
                minCat: document.getElementById('filter-catalyst').value,
                minRvol: document.getElementById('filter-rvol').value,
                minScore: document.getElementById('filter-score').value,
                selSector: document.getElementById('filter-sector').value,
                activeView: window.currentWatchlistView || 'core'
            };
            localStorage.setItem('screener_filter_prefs', JSON.stringify(prefs));
            const saveNotice = document.getElementById('save-status-pill');
            if (saveNotice) {
                saveNotice.style.display = 'inline-block';
                saveNotice.innerText = '💾 Saved';
                setTimeout(() => { saveNotice.innerText = '💾 Auto-Saved'; }, 1500);
            }
        } catch (e) {
            console.error('Failed to save filter preferences:', e);
        }
    }

    function loadFilterPreferences() {
        try {
            const saved = localStorage.getItem('screener_filter_prefs');
            if (saved) {
                const prefs = JSON.parse(saved);
                if (prefs.reqLastHigh !== undefined) document.getElementById('filter-breakout-last').checked = prefs.reqLastHigh;
                if (prefs.reqPmHigh !== undefined) document.getElementById('filter-breakout-pm').checked = prefs.reqPmHigh;
                if (prefs.filterChg !== undefined && document.getElementById('filter-chg')) document.getElementById('filter-chg').value = prefs.filterChg;
                if (prefs.minGap !== undefined && document.getElementById('filter-gap')) document.getElementById('filter-gap').value = prefs.minGap;
                if (prefs.filterOpen !== undefined && document.getElementById('filter-open')) document.getElementById('filter-open').value = prefs.filterOpen;
                if (prefs.filterVwap !== undefined && document.getElementById('filter-vwap')) document.getElementById('filter-vwap').value = prefs.filterVwap;
                if (prefs.filterFlow !== undefined && document.getElementById('filter-flow')) document.getElementById('filter-flow').value = prefs.filterFlow;
                if (prefs.filterSma20 !== undefined && document.getElementById('filter-sma20')) document.getElementById('filter-sma20').value = prefs.filterSma20;
                if (prefs.filterSma50 !== undefined && document.getElementById('filter-sma50')) document.getElementById('filter-sma50').value = prefs.filterSma50;
                if (prefs.filterSma200 !== undefined && document.getElementById('filter-sma200')) document.getElementById('filter-sma200').value = prefs.filterSma200;
                if (prefs.minCat !== undefined) document.getElementById('filter-catalyst').value = prefs.minCat;
                if (prefs.minRvol !== undefined) document.getElementById('filter-rvol').value = prefs.minRvol;
                if (prefs.minScore !== undefined) document.getElementById('filter-score').value = prefs.minScore;
                if (prefs.selSector !== undefined) {
                    const secElem = document.getElementById('filter-sector');
                    if (secElem && secElem.querySelector(`option[value="${prefs.selSector}"]`)) {
                        secElem.value = prefs.selSector;
                    }
                }
                if (prefs.activeView) {
                    switchWatchlistView(prefs.activeView, false);
                }
            }
        } catch (e) {
            console.error('Failed to load filter preferences:', e);
        }
    }

    function filterDayWatchlist(save = true) {
        const reqLastHigh = document.getElementById('filter-breakout-last').checked;
        const reqPmHigh = document.getElementById('filter-breakout-pm').checked;
        const filterChg = document.getElementById('filter-chg') ? document.getElementById('filter-chg').value : 'ALL';
        const filterGap = document.getElementById('filter-gap') ? document.getElementById('filter-gap').value : '3.0';
        const filterOpen = document.getElementById('filter-open') ? document.getElementById('filter-open').value : 'ALL';
        const filterVwap = document.getElementById('filter-vwap') ? document.getElementById('filter-vwap').value : 'ALL';
        const filterFlow = document.getElementById('filter-flow') ? document.getElementById('filter-flow').value : 'ALL';
        const filterSma20 = document.getElementById('filter-sma20') ? document.getElementById('filter-sma20').value : 'ALL';
        const filterSma50 = document.getElementById('filter-sma50') ? document.getElementById('filter-sma50').value : 'ALL';
        const filterSma200 = document.getElementById('filter-sma200') ? document.getElementById('filter-sma200').value : 'ALL';
        const minCat = parseFloat(document.getElementById('filter-catalyst').value) || 0.0;
        const minRvol = parseFloat(document.getElementById('filter-rvol').value) || 0.0;
        const minScore = parseFloat(document.getElementById('filter-score').value) || 0.0;
        const selSector = document.getElementById('filter-sector').value;
        const searchInput = document.getElementById('day-search-input');
        const q = searchInput ? searchInput.value.toLowerCase().trim() : '';

        const state = tableStates['day-table'];
        if (!state) return;

        state.filteredRows = state.allRows.filter(r => {
            const bLast = r.getAttribute('data-breakout-last') === 'true';
            const bPm = r.getAttribute('data-breakout-pm') === 'true';
            const chg = parseFloat(r.getAttribute('data-chg')) || 0.0;
            const gap = parseFloat(r.getAttribute('data-gap')) || 0.0;
            const openChg = parseFloat(r.getAttribute('data-open')) || 0.0;
            const vwapDist = parseFloat(r.getAttribute('data-vwap-dist')) || 0.0;
            const vwapXo = r.getAttribute('data-vwap-xo') === 'true';
            const vwapXu = r.getAttribute('data-vwap-xu') === 'true';
            const vwapP1 = r.getAttribute('data-vwap-std-p1') === 'true';
            const vwapP2 = r.getAttribute('data-vwap-std-p2') === 'true';
            const vwapM1 = r.getAttribute('data-vwap-std-m1') === 'true';
            const vwapM2 = r.getAttribute('data-vwap-std-m2') === 'true';

            const skew = r.getAttribute('data-skew') || 'Neutral';
            const pc = parseFloat(r.getAttribute('data-pc')) || 1.0;
            const netFlow = parseFloat(r.getAttribute('data-net-flow')) || 0.0;
            const whales = parseInt(r.getAttribute('data-whales'), 10) || 0;

            const sma20Dist = parseFloat(r.getAttribute('data-sma20-dist')) || 0.0;
            const sma20Xo = r.getAttribute('data-sma20-xo') === 'true';
            const sma20Xu = r.getAttribute('data-sma20-xu') === 'true';

            const sma50Dist = parseFloat(r.getAttribute('data-sma50-dist')) || 0.0;
            const sma50Xo = r.getAttribute('data-sma50-xo') === 'true';
            const sma50Xu = r.getAttribute('data-sma50-xu') === 'true';

            const sma200Dist = parseFloat(r.getAttribute('data-sma200-dist')) || 0.0;
            const sma200Xo = r.getAttribute('data-sma200-xo') === 'true';
            const sma200Xu = r.getAttribute('data-sma200-xu') === 'true';

            const stars = parseFloat(r.getAttribute('data-stars')) || 0.0;
            const isPos = r.getAttribute('data-pos') === 'true';
            const rvol = parseFloat(r.getAttribute('data-rvol')) || 0.0;
            const score = parseFloat(r.getAttribute('data-score')) || 0.0;
            const sector = r.getAttribute('data-sector') || '';
            const text = r.innerText.toLowerCase();

            if (reqLastHigh && !bLast) return false;
            if (reqPmHigh && !bPm) return false;

            if (filterChg !== 'ALL') {
                if (filterChg === 'POS' && chg <= 0) return false;
                if (filterChg === 'NEG' && chg >= 0) return false;
                if (filterChg !== 'POS' && filterChg !== 'NEG') {
                    const minChg = parseFloat(filterChg);
                    if (!isNaN(minChg) && chg < minChg) return false;
                }
            }

            if (filterGap !== 'ALL') {
                if (filterGap === 'NOGAP') {
                    if (gap < -0.99 || gap > 0.99) return false;
                } else {
                    const numGap = parseFloat(filterGap);
                    if (!isNaN(numGap)) {
                        if (numGap < 0) {
                            if (gap > numGap) return false;
                        } else {
                            if (gap < numGap) return false;
                        }
                    }
                }
            }

            if (filterOpen !== 'ALL') {
                if (filterOpen === 'POS' && openChg <= 0) return false;
                if (filterOpen === 'NEG' && openChg >= 0) return false;
                if (filterOpen !== 'POS' && filterOpen !== 'NEG') {
                    const minOpen = parseFloat(filterOpen);
                    if (!isNaN(minOpen) && openChg < minOpen) return false;
                }
            }

            if (filterVwap !== 'ALL') {
                if (filterVwap === 'POS' && vwapDist < 0) return false;
                if (filterVwap === 'NEG' && vwapDist >= 0) return false;
                if (filterVwap === 'XO') {
                    if (!vwapXo && !(vwapDist >= 0 && vwapDist <= 1.5)) return false;
                } else if (filterVwap === 'XU') {
                    if (!vwapXu && !(vwapDist <= 0 && vwapDist >= -1.5)) return false;
                } else if (filterVwap === 'STD_P1') {
                    if (!vwapP1 && vwapDist < 1.0) return false;
                } else if (filterVwap === 'STD_P2') {
                    if (!vwapP2 && vwapDist < 2.0) return false;
                } else if (filterVwap === 'STD_M1') {
                    if (!vwapM1 && vwapDist > -1.0) return false;
                } else if (filterVwap === 'STD_M2') {
                    if (!vwapM2 && vwapDist > -2.0) return false;
                } else if (filterVwap !== 'POS' && filterVwap !== 'NEG') {
                    const minVwap = parseFloat(filterVwap);
                    if (!isNaN(minVwap) && vwapDist < minVwap) return false;
                }
            }

            if (filterFlow !== 'ALL') {
                if (filterFlow === 'BULL_FLOW') {
                    if (!skew.includes('Bullish') && pc >= 0.70 && netFlow <= 0) return false;
                } else if (filterFlow === 'BEAR_FLOW') {
                    if (!skew.includes('Bearish') && pc <= 1.00 && netFlow >= 0) return false;
                } else if (filterFlow === 'WHALE') {
                    if (whales <= 0) return false;
                } else if (filterFlow === 'MOM_BULL') {
                    if (vwapDist < 0 || (!skew.includes('Bullish') && pc >= 0.85 && netFlow <= 0)) return false;
                } else if (filterFlow === 'MOM_BEAR') {
                    if (vwapDist >= 0 || (!skew.includes('Bearish') && pc <= 1.00 && netFlow >= 0)) return false;
                }
            }

            if (filterSma20 !== 'ALL') {
                if (filterSma20 === 'POS' && sma20Dist < 0) return false;
                if (filterSma20 === 'NEG' && sma20Dist >= 0) return false;
                if (filterSma20 === 'XO') {
                    if (!sma20Xo && !(sma20Dist >= 0 && sma20Dist <= 1.5)) return false;
                } else if (filterSma20 === 'XU') {
                    if (!sma20Xu && !(sma20Dist <= 0 && sma20Dist >= -1.5)) return false;
                } else if (filterSma20 !== 'POS' && filterSma20 !== 'NEG') {
                    const minSma = parseFloat(filterSma20);
                    if (!isNaN(minSma) && sma20Dist < minSma) return false;
                }
            }

            if (filterSma50 !== 'ALL') {
                if (filterSma50 === 'POS' && sma50Dist < 0) return false;
                if (filterSma50 === 'NEG' && sma50Dist >= 0) return false;
                if (filterSma50 === 'XO') {
                    if (!sma50Xo && !(sma50Dist >= 0 && sma50Dist <= 1.5)) return false;
                } else if (filterSma50 === 'XU') {
                    if (!sma50Xu && !(sma50Dist <= 0 && sma50Dist >= -1.5)) return false;
                } else if (filterSma50 !== 'POS' && filterSma50 !== 'NEG') {
                    const minSma = parseFloat(filterSma50);
                    if (!isNaN(minSma) && sma50Dist < minSma) return false;
                }
            }

            if (filterSma200 !== 'ALL') {
                if (filterSma200 === 'POS' && sma200Dist < 0) return false;
                if (filterSma200 === 'NEG' && sma200Dist >= 0) return false;
                if (filterSma200 === 'XO') {
                    if (!sma200Xo && !(sma200Dist >= 0 && sma200Dist <= 1.5)) return false;
                } else if (filterSma200 === 'XU') {
                    if (!sma200Xu && !(sma200Dist <= 0 && sma200Dist >= -1.5)) return false;
                } else if (filterSma200 !== 'POS' && filterSma200 !== 'NEG') {
                    const minSma = parseFloat(filterSma200);
                    if (!isNaN(minSma) && sma200Dist < minSma) return false;
                }
            }

            if (minCat > 0 && (!isPos || stars < minCat)) return false;
            if (rvol < minRvol) return false;
            if (score < minScore) return false;
            if (selSector !== 'ALL' && !sector.toLowerCase().includes(selSector.toLowerCase())) return false;
            if (q && !text.includes(q)) return false;

            return true;
        });

        state.currentPage = 1;
        renderTablePage('day-table');

        const visCount = document.getElementById('day-visible-count');
        if (visCount) visCount.innerText = state.filteredRows.length;
        const totCount = document.getElementById('day-total-count');
        if (totCount) totCount.innerText = state.allRows.length;

        if (save) {
            saveFilterPreferences();
        }
    }

    function resetInstitutionalDefaults() {
        document.getElementById('filter-breakout-last').checked = true;
        document.getElementById('filter-breakout-pm').checked = true;
        if (document.getElementById('filter-chg')) document.getElementById('filter-chg').value = "ALL";
        if (document.getElementById('filter-gap')) document.getElementById('filter-gap').value = "3.0";
        if (document.getElementById('filter-open')) document.getElementById('filter-open').value = "ALL";
        if (document.getElementById('filter-vwap')) document.getElementById('filter-vwap').value = "ALL";
        if (document.getElementById('filter-flow')) document.getElementById('filter-flow').value = "ALL";
        if (document.getElementById('filter-sma20')) document.getElementById('filter-sma20').value = "ALL";
        if (document.getElementById('filter-sma50')) document.getElementById('filter-sma50').value = "ALL";
        if (document.getElementById('filter-sma200')) document.getElementById('filter-sma200').value = "ALL";
        document.getElementById('filter-catalyst').value = "2.0";
        document.getElementById('filter-rvol').value = "1.5";
        document.getElementById('filter-score').value = "2.5";
        document.getElementById('filter-sector').value = "ALL";
        const searchInput = document.getElementById('day-search-input');
        if (searchInput) searchInput.value = '';
        filterDayWatchlist(true);
    }

    function showAllCandidates() {
        document.getElementById('filter-breakout-last').checked = false;
        document.getElementById('filter-breakout-pm').checked = false;
        if (document.getElementById('filter-chg')) document.getElementById('filter-chg').value = "ALL";
        if (document.getElementById('filter-gap')) document.getElementById('filter-gap').value = "ALL";
        if (document.getElementById('filter-open')) document.getElementById('filter-open').value = "ALL";
        if (document.getElementById('filter-vwap')) document.getElementById('filter-vwap').value = "ALL";
        if (document.getElementById('filter-flow')) document.getElementById('filter-flow').value = "ALL";
        if (document.getElementById('filter-sma20')) document.getElementById('filter-sma20').value = "ALL";
        if (document.getElementById('filter-sma50')) document.getElementById('filter-sma50').value = "ALL";
        if (document.getElementById('filter-sma200')) document.getElementById('filter-sma200').value = "ALL";
        document.getElementById('filter-catalyst').value = "0.0";
        document.getElementById('filter-rvol').value = "0.0";
        document.getElementById('filter-score').value = "0.0";
        document.getElementById('filter-sector').value = "ALL";
        const searchInput = document.getElementById('day-search-input');
        if (searchInput) searchInput.value = '';
        filterDayWatchlist(true);
    }
