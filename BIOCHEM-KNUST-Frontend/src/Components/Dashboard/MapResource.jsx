import { useEffect, useRef } from "react";
import { Clock, FileText, MapPin } from "lucide-react";
import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";
import pin from "../../assets/pin.png";
import { format } from "date-fns";

const customIcon = L.icon({
  iconUrl: pin,
  iconSize: [30, 30],
  iconAnchor: [15, 30],
  popupAnchor: [0, -30],
});

export function MapResource({ selectedExam }) {
  const mapRef = useRef();

  // Parse and validate geolocation
  const getValidCoordinates = () => {
    if (!selectedExam?.geolocation) return null;
    const coords = selectedExam.geolocation.split(",");
    const lat = parseFloat(coords[0]);
    const lng = parseFloat(coords[1]);
    if (isNaN(lat) || isNaN(lng)) return null;
    return [lat, lng];
  };

  const coordinates = getValidCoordinates();

  useEffect(() => {
    if (mapRef.current && coordinates) {
      const mapInstance = mapRef.current;
      mapInstance.setView(coordinates, 50);
    }
  }, [selectedExam?.geolocation]);

  return (
    Object.keys(selectedExam) != 0 && (
      <div className="bg-white h-full w-[100%] rounded-xl p-6 shadow-lg border gap-4 border-gray-100">
        <h2 className="text-2xl font-bold text-gray-900 mb-3">Map View</h2>

        <div className="flex flex-col justify-center  gap-1 mb-3">
          <div className="flex flex-row items-center gap-2">
            <FileText className="w-4 h-4 text-blue-600" />
            <h3 className="font-medium text-gray-900">
              {selectedExam?.course?.course_name} - (
              {selectedExam?.course?.course_code})
            </h3>
          </div>
          <div className="flex flex-row items-center gap-2">
            <MapPin className="w-4 h-4 text-blue-600" />
            <h3 className="font-medium text-gray-700">
              {selectedExam?.college} - {selectedExam?.room}
            </h3>
          </div>
          <div className="flex flex-row items-center gap-2">
            <Clock className="w-4 h-4 text-blue-600" />
            <p className="text-sm text-gray-600">
              {format(new Date(selectedExam?.date), "MMMM d, yyyy") +
                " " +
                format(new Date(selectedExam?.time), "hh:mm a")}
            </p>
          </div>
        </div>

        <div className="h-64 rounded-lg overflow-hidden border border-gray-200">
          {coordinates ? (
            <MapContainer
              center={coordinates}
              zoom={50}
              scrollWheelZoom={false}
              ref={mapRef}
              className="w-full h-full"
            >
              <TileLayer
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              />
              <Marker position={coordinates} icon={customIcon}>
                <Popup>{selectedExam?.course?.course_name}</Popup>
              </Marker>
            </MapContainer>
          ) : (
            <div className="w-full h-full flex items-center justify-center bg-gray-100">
              <div className="text-center">
                <MapPin className="w-12 h-12 text-gray-400 mx-auto mb-2" />
                <p className="text-gray-600 text-sm">Location not available</p>
              </div>
            </div>
          )}
        </div>
      </div>
    )
  );
}
