import React, {
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
} from "react";
import { Calendar, Clock, MapPin, BookOpen } from "lucide-react";
import { MapContainer, TileLayer, Marker, useMap } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";
import ExamTile from "./ExamTile";
import pin from "../../assets/pin.png";
import { useExams } from "../../Context/ExamsContext";
import { UserContext } from "../../Context/UserContext";
import useAxiosWithRefresh from "../../Hooks/useAxiosWithRefresh";
import { BACKEND_HOST } from "../../utils/config";
import { scrollToTop } from "../../utils/scrollToTop";
import ExamTileSkeleton from "./ExamTileSkeleton";

const customIcon = L.icon({
  iconUrl: pin,
  iconSize: [30, 30],
  iconAnchor: [15, 30],
  popupAnchor: [0, -30],
});

function MapUpdater({ latitude, longitude }) {
  const map = useMap();
  useEffect(() => {
    map.setView([latitude, longitude], 50, { animate: true });
  }, [latitude, longitude, map]);
  return null;
}

export function ExamSchedule() {
  const mapRef = useRef();
  const { exams, setExams } = useExams();
  const { user } = useContext(UserContext);
  const axiosInstance = useAxiosWithRefresh();
  const [isLoading, setIsLoading] = useState(true);
  const [selectedExam, setSelectedExam] = useState({
    latitude: parseFloat("6.673137532517488"),
    longitude: parseFloat("-1.5671843379287753"),
  });

  const handleExamClick = (exam) => {
    const [latitude, longitude] = exam?.geolocation
      ?.split(",")
      ?.map(parseFloat);
    setSelectedExam({ latitude, longitude });
  };

  const fetchExams = useCallback(async () => {
    if (user?.access) {
      try {
        setIsLoading(true);
        const response = await axiosInstance.get(
          `${BACKEND_HOST}/timetable_system/schedules/`,
          {
            headers: { Authorization: `Bearer ${user.access}` },
          }
        );

        // New endpoint returns {status, message, data, meta}
        const examsData = response.data?.data || [];
        const formattedExams = examsData.map((exam) => ({
          course: exam?.course,
          time: exam?.time,
          college: exam?.college,
          room: exam?.room,
          geolocation: exam.geolocation,
          date: exam?.time.split("T")[0],
        }));
        setExams(formattedExams || []);
      } catch (error) {
        console.error("Failed to fetch exams:", error);
        setExams([]);
      } finally {
        setIsLoading(false);
      }
    }
  }, [user, axiosInstance, setExams]);

  useEffect(() => {
    scrollToTop();
    fetchExams();
  }, []);

  // useEffect(() => {
  //   if (mapRef.current) {
  //     mapRef.current.setView(
  //       [selectedExam.latitude, selectedExam.longitude],
  //       50,
  //       { animate: true }
  //     );
  //   }
  // }, [selectedExam]);

  const [modalOpen, setModalOpen] = useState(false);

  const openModal = () => {
    setModalOpen(true);
  };

  const closeModal = () => {
    setModalOpen(false);
  };

  return (
    <>
      {exams.length != 0 && (
        <p className="text-gray-400 md:block hidden font-semibold">
          Click on marker for map direction
        </p>
      )}
      <div className="flex gap-8">
        <div className="flex-1 w-2/3 flex flex-col gap-4">
          {exams.length != 0 && (
            <p className="text-gray-400 text-center md:hidden font-semibold">
              Click on marker to show map
            </p>
          )}
          {exams.length != 0 && isLoading ? (
            exams?.map((exam, index) => (
              <ExamTile
                key={index}
                exam={exam}
                openModal={openModal}
                onClick={() => handleExamClick(exam)}
              />
            ))
          ) : isLoading ? (
            Array.from({ length: 3 }).map((_, index) => (
              <ExamTileSkeleton key={index} />
            ))
          ) : exams.length == 0 ? (
            <p className="text-gray-600 text-center mt-16 text-2xl font-bold">
              No exams schedule yet.
            </p>
          ) : (
            exams?.map((exam, index) => (
              <ExamTile
                key={index}
                exam={exam}
                openModal={openModal}
                onClick={() => handleExamClick(exam)}
              />
            ))
          )}
        </div>

        <div className="w-1/3 hidden md:block">
          <div className="rounded-lg overflow-hidden shadow-lg">
            <MapContainer
              center={[selectedExam.latitude, selectedExam.longitude]}
              zoom={50}
              style={{ height: "500px", width: "100%" }}
              // ref={mapRef}
            >
              <MapUpdater
                latitude={selectedExam.latitude}
                longitude={selectedExam.longitude}
              />
              <TileLayer
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              />
              <Marker
                position={[selectedExam.latitude, selectedExam.longitude]}
                icon={customIcon}
              />
            </MapContainer>
          </div>
        </div>
      </div>
      {modalOpen && (
        <div className="fixed inset-0 -top-10 md:hidden bg-black bg-opacity-75 flex items-center justify-center z-[6001]">
          <div className="relative w-[90%] md:w-2/3">
            <button
              onClick={closeModal}
              className="absolute top-2 right-2 z-[6000] font-bold rounded-full text-red-500 p-2 px-[14px] bg-black/50 hover:text-red-800"
            >
              ✕
            </button>
            <MapContainer
              center={[selectedExam.latitude, selectedExam.longitude]}
              zoom={50}
              style={{ height: "500px", width: "100%" }}
              // ref={mapRef}
            >
              <MapUpdater
                latitude={selectedExam.latitude}
                longitude={selectedExam.longitude}
              />
              <TileLayer
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              />
              <Marker
                position={[selectedExam.latitude, selectedExam.longitude]}
                icon={customIcon}
              />
            </MapContainer>
          </div>
        </div>
      )}
    </>
  );
}
