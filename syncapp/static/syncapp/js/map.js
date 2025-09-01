document.addEventListener("DOMContentLoaded", function () {
    loadConsumers();
});

function loadConsumers() {
    fetch("/consumers_geojson")
        .then(response => response.json())
        .then(data => {
            console.log("Consumers GeoJSON:", data);

            const userSelect = document.getElementById("consumerSelect");
            userSelect.innerHTML = "<option value=''>Select a Consumer</option>";

            data.features.forEach(feature => {
                const name = feature.properties.name || "Unnamed";
                const id = feature.properties.id;

                // Add to user dropdown
                const opt = document.createElement("option");
                opt.value = id;
                opt.textContent = name;
                userSelect.appendChild(opt);
            });

            // Map all consumers for later use
            window.allConsumers = data.features;

            // Show all on map
            renderMap(data.features);
        })
        .catch(err => console.error("Error loading consumers:", err));
}

function renderMap(features) {
    if (!window.map) {
        window.map = L.map("map").setView([19.7515, 75.7139], 7); // Maharashtra
        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
            maxZoom: 18,
            attribution: "© OpenStreetMap"
        }).addTo(window.map);
    }

    if (window.geoLayer) {
        window.map.removeLayer(window.geoLayer);
    }

    window.geoLayer = L.geoJSON(features, {
        onEachFeature: function (feature, layer) {
            if (feature.properties && feature.properties.name) {
                let popupContent = `<strong>Name:</strong> ${feature.properties.name}<br>`;

                let pdata = feature.properties.data;
                if (typeof pdata === "string") {
                    try {
                        pdata = JSON.parse(pdata);
                    } catch {
                        pdata = {};
                    }
                }

                if (pdata.date) {
                    popupContent += `<strong>Date:</strong> ${new Date(pdata.date).toLocaleString()}<br>`;
                }
                if (pdata.pricePerUnit) {
                    popupContent += `<strong>Price per Unit:</strong> ${pdata.pricePerUnit}<br>`;
                }

                layer.bindPopup(popupContent);
            }
        }
    }).addTo(window.map);
}

// When a consumer is selected → populate products dropdown
document.getElementById("consumerSelect").addEventListener("change", function () {
    const selectedId = this.value;
    const productSelect = document.getElementById("productSelect");
    productSelect.innerHTML = "<option value=''>Select a Product</option>";

    if (!selectedId) return;

    const feature = window.allConsumers.find(f => f.properties.id == selectedId);
    if (!feature) return;

    let pdata = feature.properties.data;
    if (typeof pdata === "string") {
        try {
            pdata = JSON.parse(pdata);
        } catch {
            pdata = {};
        }
    }

    if (pdata.products && Array.isArray(pdata.products)) {
        pdata.products.forEach(prod => {
            const opt = document.createElement("option");
            opt.value = prod.name;
            opt.textContent = prod.name;
            productSelect.appendChild(opt);
        });
    }
});
