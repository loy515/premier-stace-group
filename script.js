// This function is the single entry point for our entire page.
// It is called by the Google Maps API script only when it is fully loaded and ready.
function initApp() {
    console.log("SUCCESS: Google Maps API is ready. The application is now starting.");

    // --- 1. GRAB DATA ---
    // Read the shipment data that was embedded directly into the HTML page.
    const shipmentData = window.SHIPMENT_DATA;
    if (!shipmentData) {
        console.error("CRITICAL ERROR: The SHIPMENT_DATA object was not found. Check the <script> tag in tracking_result.html.");
        return;
    }

    // --- 2. GRAB HTML ELEMENTS ---
    const mapDiv = document.getElementById('map');
    const verifyBtn = document.getElementById('verify-btn');
    const correctionFormContainer = document.getElementById('correction-form-container');
    const addressDisplay = document.getElementById('address-display');
    
    // --- 3. INITIALIZE THE MAP ---
    const packageLocation = { lat: parseFloat(shipmentData.CurrentLocation_Lat), lng: parseFloat(shipmentData.CurrentLocation_Lon) };
    const map = new google.maps.Map(mapDiv, {
        zoom: 4,
        center: packageLocation,
    });

    // --- 4. CREATE MAP MARKERS ---
    // Create the blue dot for the package's physical location.
    if (packageLocation.lat || packageLocation.lng) {
        new google.maps.Marker({
            position: packageLocation,
            map: map,
            title: `Package Location: ${shipmentData.CurrentLocation_City}`,
            icon: 'http://maps.google.com/mapfiles/ms/icons/blue-dot.png'
        });
    }
    let destinationMarker; // This will hold the red dot for the destination.

    // --- 5. HELPER FUNCTION TO GEOCODE AN ADDRESS AND UPDATE THE MAP ---
    async function updateMapToAddress(address) {
        try {
            const response = await fetch(`/geocode?address=${encodeURIComponent(address)}`);
            if (!response.ok) throw new Error('Geocoding request failed');
            const destinationCoords = await response.json();
            if (destinationCoords.error) throw new Error(destinationCoords.error);

            if (!destinationMarker) {
                destinationMarker = new google.maps.Marker({ position: destinationCoords, map: map, title: `Destination: ${address}` });
            } else {
                destinationMarker.setPosition(destinationCoords);
            }
            map.setCenter(destinationCoords);
            map.setZoom(12);
        } catch (error) {
            console.error("Map Update Failed:", error);
            addressDisplay.innerHTML += "<br><small style='color:red;'>Could not locate this address on the map.</small>";
        }
    }

    // --- 6. ATTACH THE CLICK EVENT TO THE 'VERIFY' BUTTON ---
    verifyBtn.addEventListener('click', async () => {
        verifyBtn.disabled = true;
        verifyBtn.textContent = 'Verifying...';

        const formData = new FormData();
        formData.append('address', shipmentData.RecipientAddress);
        formData.append('shipment_id', shipmentData.ShipmentID);

        try {
            const response = await fetch('/verify_address', { method: 'POST', body: formData });
            const data = await response.text();
            
            addressDisplay.textContent = data;
            verifyBtn.style.display = 'none';
            correctionFormContainer.style.display = 'block';
            await updateMapToAddress(data);
        } catch (error) {
            console.error("Verification Fetch Error:", error);
            addressDisplay.textContent = "Error during verification. See console.";
            verifyBtn.disabled = false;
            verifyBtn.textContent = 'Verify Destination';
        }
    });

    // --- 7. REACTIVE LOGIC ON INITIAL PAGE LOAD ---
    // This code runs once the map and buttons are all set up.
    const verifiedAddress = shipmentData.VerifiedAddress?.trim();
    if (verifiedAddress && verifiedAddress.length > 5 && verifiedAddress !== 'Not yet verified.') {
        verifyBtn.style.display = 'none';
        correctionFormContainer.style.display = 'block';
        updateMapToAddress(verifiedAddress);
    }
    console.log("SUCCESS: Application initialized. All components are live.");
}
