
export default function DotBackground({children}) {
  return (
    (<div
      className=" w-full bg-white  dark:bg-dot-white/[0.5] bg-dot-black/[0.3] relative flex flex-col items-center justify-center">
      <div
        className="absolute pointer-events-none inset-0 flex items-center justify-center dark:bg-black bg-white [mask-image:radial-gradient(ellipse_at_center,transparent_20%,black)]"></div>
      {children}
    </div>)
  );
}
