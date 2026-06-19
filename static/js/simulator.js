document.addEventListener('DOMContentLoaded', () => {
    // --- Form Loading State ---
    const form = document.getElementById('footprint-form');
    const calculateBtn = document.getElementById('calculate-btn');

    if (form) {
        form.addEventListener('submit', () => {
            calculateBtn.classList.add('btn-loading');
            calculateBtn.style.position = 'relative';
        });
    }

    // --- Interactive Charts & What-If Simulator ---
    if (window.FOOTPRINT_DATA) {
        const data = window.FOOTPRINT_DATA;
        const breakdown = data.breakdown;
        const inputs = data.inputs;

        // Colors matching our CSS variables
        const colors = {
            travel: '#f44336',
            food: '#ff9800',
            energy: '#2196f3',
            waste: '#9c27b0',
            goods: '#009688',
            digital: '#607d8b',
            healthcare: '#e91e63'
        };

        // --- 1. Category Doughnut Chart ---
        const categoryCtx = document.getElementById('categoryChart').getContext('2d');
        const categoryLabels = ['Travel', 'Food & Diet', 'Energy', 'General Waste', 'Food Waste', 'Goods', 'Digital', 'Healthcare'];
        const categoryData = [
            breakdown.travel,
            breakdown.food,
            breakdown.energy,
            breakdown.waste,
            breakdown.food_waste,
            breakdown.goods,
            breakdown.digital,
            breakdown.healthcare
        ];

        const isDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
        const textStyle = {
            color: isDark ? '#aaaaaa' : '#666666',
            font: { family: 'Outfit, sans-serif', size: 12 }
        };

        const categoryChart = new Chart(categoryCtx, {
            type: 'doughnut',
            data: {
                labels: categoryLabels,
                datasets: [{
                    data: categoryData,
                    backgroundColor: Object.values(colors),
                    borderWidth: isDark ? 2 : 1,
                    borderColor: isDark ? '#1e1e1e' : '#ffffff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: textStyle
                    },
                    tooltip: {
                        callbacks: {
                            label: (context) => {
                                const val = context.raw;
                                const sum = context.dataset.data.reduce((a, b) => a + b, 0);
                                const pct = ((val / sum) * 100).toFixed(1);
                                return `${context.label}: ${val.toFixed(1)} kg (${pct}%)`;
                            }
                        }
                    }
                }
            }
        });

        // --- 2. Benchmark Comparison Bar Chart ---
        const benchmarkCtx = document.getElementById('benchmarkChart').getContext('2d');
        const userTons = data.total_yearly_tons;

        const benchmarkChart = new Chart(benchmarkCtx, {
            type: 'bar',
            data: {
                labels: ['Your Footprint', 'U.S. Average', 'Global Average', 'Paris Target', 'Top 1%'],
                datasets: [{
                    label: 'Tons CO₂e/yr',
                    data: [userTons, 17.6, 6.6, 2.3, 74.0],
                    backgroundColor: [
                        userTons > 17.6 ? '#d32f2f' : '#2e7d32',
                        '#8d6e63',
                        '#78909c',
                        '#388e3c',
                        '#37474f'
                    ],
                    borderRadius: 6
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        grid: { color: isDark ? '#333333' : '#e0e0e0' },
                        ticks: textStyle
                    },
                    y: {
                        grid: { display: false },
                        ticks: textStyle
                    }
                },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: (context) => `${context.raw} Tons CO₂e/yr`
                        }
                    }
                }
            }
        });

        // --- 3. What-If Simulator Logic ---
        const simDrive = document.getElementById('sim-drive');
        const simDriveVal = document.getElementById('sim-drive-val');
        const simSpeedLimit = document.getElementById('sim-speed-limit');
        const simLed = document.getElementById('sim-led');
        const simStandby = document.getElementById('sim-standby');
        const simColdWash = document.getElementById('sim-cold-wash');
        const simMealKits = document.getElementById('sim-meal-kits');
        const simSolarRoof = document.getElementById('sim-solar-roof');
        const simFurnitureRefurb = document.getElementById('sim-furniture-refurb');

        const simTotalTonsEl = document.getElementById('sim-total-tons');
        const savingsAmountEl = document.getElementById('savings-amount');
        const savingsBox = document.getElementById('savings-box');

        // Dynamic trees/cars numbers
        const treesNumEl = document.getElementById('trees-eq-num');
        const carsNumEl = document.getElementById('cars-eq-num');

        // Factor values
        const travelFactor = {
            "car": 0.304,
            "flight": 0.186,
            "car_electric": 0.0,
            "bus": 0.08,
            "motorbike": 0.05
        };

        const goodsFactors = {
            "clothing": 5.0,
            "furniture": 50.0,
            "electronics": 20.0
        };

        function updateSimulator() {
            // Read input parameters
            const baseTravel = breakdown.travel;
            const baseFood = breakdown.food;
            const baseEnergy = breakdown.energy;
            const baseGoods = breakdown.goods;
            const baseWaste = breakdown.waste + breakdown.food_waste;
            const baseDigital = breakdown.digital;
            const baseHealthcare = breakdown.healthcare;

            // Travel adjustments
            const driveReduction = parseInt(simDrive.value, 10);
            simDriveVal.innerText = driveReduction;

            // 1. Calculate new travel emissions
            let newTravel = baseTravel * (1 - (driveReduction / 100));
            if (simSpeedLimit.checked && inputs.mode !== 'flight') {
                newTravel = newTravel * 0.90; // Saves 10% fuel
            }

            // 2. Calculate new food emissions
            let newFood = baseFood;
            // Only apply meal kit discount if not already selected in input form
            if (simMealKits.checked && inputs.cooking_style !== 'meal_kits') {
                newFood = baseFood * 0.67; // 33% discount
            }

            // 3. Calculate new energy emissions
            let newEnergy = baseEnergy;
            if (simSolarRoof.checked) {
                newEnergy = baseEnergy * 0.9325; // 27% savings on cooling, assuming 25% of energy is cooling
            }

            // 4. Calculate new goods emissions
            let newGoods = baseGoods;
            if (simFurnitureRefurb.checked) {
                // Deduct 85% of furniture contribution
                const furnitureContrib = (inputs.furniture * goodsFactors.furniture) / 12.0;
                newGoods = baseGoods - (furnitureContrib * 0.85);
            }

            // 5. Deduct flat additions (LED, standby, cold washing) converted to monthly kg
            // LED saves 500 kg CO2e / yr
            const ledSavings = simLed.checked ? (500 / 12.0) : 0;
            // Standby saves 200 kg CO2e / yr
            const standbySavings = simStandby.checked ? (200 / 12.0) : 0;
            // Cold washing saves 32 kg CO2e / yr
            const coldWashSavings = simColdWash.checked ? (32 / 12.0) : 0;

            let newTotalMonthly = (newTravel + newFood + newEnergy + newGoods + baseWaste + baseDigital + baseHealthcare) 
                                  - ledSavings - standbySavings - coldWashSavings;

            if (newTotalMonthly < 0) newTotalMonthly = 0;

            const newTotalYearlyTons = (newTotalMonthly * 12) / 1000;
            const savingsYearlyKg = (data.total_monthly_kg - newTotalMonthly) * 12;

            // Update UI elements
            simTotalTonsEl.innerText = newTotalYearlyTons.toFixed(2);
            savingsAmountEl.innerText = `${savingsYearlyKg.toFixed(1)} kg CO₂e`;

            // Update Environmental Equivalents based on new footprint
            const newTrees = Math.round((newTotalMonthly * 12) / 48);
            const newCars = (newTotalYearlyTons / 4.6).toFixed(1);
            treesNumEl.innerText = newTrees;
            carsNumEl.innerText = newCars;

            // Highlight savings
            if (savingsYearlyKg > 50) {
                savingsBox.classList.add('active');
            } else {
                savingsBox.classList.remove('active');
            }
        }

        // Attach event listeners to all simulator components
        simDrive.addEventListener('input', updateSimulator);
        simSpeedLimit.addEventListener('change', updateSimulator);
        simLed.addEventListener('change', updateSimulator);
        simStandby.addEventListener('change', updateSimulator);
        simColdWash.addEventListener('change', updateSimulator);
        if (inputs.cooking_style !== 'meal_kits') {
            simMealKits.addEventListener('change', updateSimulator);
        }
        simSolarRoof.addEventListener('change', updateSimulator);
        simFurnitureRefurb.addEventListener('change', updateSimulator);

        // Smooth scroll to results on screen load for smaller viewports
        if (window.innerWidth < 768) {
            document.querySelector('.results-hero-card').scrollIntoView({ behavior: 'smooth' });
        }
    }
});
