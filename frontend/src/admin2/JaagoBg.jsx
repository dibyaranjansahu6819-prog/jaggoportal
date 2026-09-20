import "./JaagoBg.css";

const PETAL = "M100 100 C 92 70, 92 35, 100 15 C 108 35, 108 70, 100 100 Z";

function Flower({ color, petals, ring, size, className }) {
  return (
    <svg className={`jb-corner ${className}`} width={size} height={size} viewBox="0 0 200 200" fill="none" aria-hidden="true">
      <g className="jb-flower-spin">
        {petals.map((deg) => (
          <g key={deg} transform={`rotate(${deg} 100 100)`}>
            <path d={PETAL} stroke={color} strokeWidth="1.4" fill="none" opacity="0.55" />
            <circle cx="100" cy="28" r="4" fill={color} opacity="0.5" />
          </g>
        ))}
        <circle cx="100" cy="100" r="10" fill={color} opacity="0.35" />
        {ring && <circle cx="100" cy="100" r="34" stroke={color} strokeWidth="1" fill="none" opacity="0.3" strokeDasharray="3 5" />}
      </g>
    </svg>
  );
}

export default function JaagoBg() {
  return (
    <>
      <img className="jb-watermark" src="/jaago-bg-watermark.png" alt="" aria-hidden="true" />
      <Flower className="jb-corner-tr" color="#b5822f" size={260} petals={[0, 45, 90, 135, 180, 225, 270, 315]} ring />
      <Flower className="jb-corner-bl" color="#7c3aed" size={220} petals={[0, 90, 180, 270]} />
    </>
  );
}
