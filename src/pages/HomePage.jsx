import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";

export default function HomePage() {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const [faces, setFaces] = useState([]);
  const navigate = useNavigate(); // React Router hook

  useEffect(() => {
    // Start webcam
    navigator.mediaDevices.getUserMedia({ video: true }).then(stream => {
      if (videoRef.current) videoRef.current.srcObject = stream;
    });
  }, []);

  useEffect(() => {
    const interval = setInterval(async () => {
      if (!videoRef.current || videoRef.current.readyState !== 4) return;

      const canvas = canvasRef.current;
      const ctx = canvas.getContext("2d");
      canvas.width = videoRef.current.videoWidth;
      canvas.height = videoRef.current.videoHeight;
      ctx.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);

      const imageData = canvas.toDataURL("image/jpeg");

      try {
        const res = await axios.post("http://localhost:5000/recognize", { image: imageData });
        setFaces(res.data.faces);

        ctx.lineWidth = 2;
        ctx.font = "16px Arial";
        ctx.textBaseline = "top";

        res.data.faces.forEach(face => {
          const [x, y, w, h] = face.bbox;
          ctx.strokeStyle = "lime";
          ctx.strokeRect(x, y, w, h);
          ctx.fillStyle = "lime";
          ctx.fillText(face.name, x, y - 20 < 0 ? y + 5 : y - 20);
        });

      } catch (err) {
        console.log("Recognition error:", err);
      }

    }, 1000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex flex-col items-center bg-gray-900 text-white min-h-screen p-4">
      <h1 className="text-3xl font-bold mb-4">Versalite</h1>

      {/* Video + Canvas */}
      <div className="relative w-[350px] h-[250px] rounded-xl mb-4">
        <video ref={videoRef} autoPlay playsInline className="absolute top-0 left-0 w-full h-full rounded-xl" />
        <canvas ref={canvasRef} className="absolute top-0 left-0 w-full h-full rounded-xl" />
      </div>

      {/* Navigation Buttons */}
      <div className="flex gap-4 mb-4">
        <button
          onClick={() => navigate("/enroll")}
          className="bg-blue-600 px-4 py-2 rounded-lg"
        >
          Enroll
        </button>
        <button
          onClick={() => navigate("/admin")}
          className="bg-green-600 px-4 py-2 rounded-lg"
        >
          Admin
        </button>
      </div>

      {/* Detected faces */}
      {faces.map((f, i) => (
        <p key={i}>{f.name} detected</p>
      ))}
    </div>
  );
}
