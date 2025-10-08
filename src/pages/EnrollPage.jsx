import { useRef, useState, useEffect } from "react";
import axios from "axios";

export default function EnrollPage() {
  const videoRef = useRef(null);
  const [name, setName] = useState("");

  useEffect(() => {
    navigator.mediaDevices.getUserMedia({ video: true }).then(stream => {
      if (videoRef.current) videoRef.current.srcObject = stream;
    });
  }, []);

  const handleEnroll = async () => {
    if (!name) return alert("Enter a name first");
    const canvas = document.createElement("canvas");
    canvas.width = videoRef.current.videoWidth;
    canvas.height = videoRef.current.videoHeight;
    canvas.getContext("2d").drawImage(videoRef.current, 0, 0);
    const imageData = canvas.toDataURL("image/jpeg");

    const res = await axios.post("http://localhost:5000/enroll", { name, image: imageData });
    alert(res.data.message);
  };

  return (
    <div className="flex flex-col items-center bg-gray-900 text-white min-h-screen p-4">
      <h1 className="text-4xl font-bold mb-4">Enroll New User</h1>
      <video ref={videoRef} autoPlay playsInline className="w-[350px] h-[250px] rounded-xl mb-4" />
      <input
        value={name}
        onChange={e => setName(e.target.value)}
        placeholder="Enter name"
        className="text-black px-3 py-2 mb-4 rounded"
      />
      <button onClick={handleEnroll} className="bg-green-600 px-5 py-2 rounded-lg">Enroll Face</button>
    </div>
  );
}
