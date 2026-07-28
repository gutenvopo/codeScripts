import logo from '../assets/logo.png'

export function BrandLogo() {
  return (
    <div
      className="relative isolate flex h-48 w-[48rem] max-w-[88vw] items-center justify-center overflow-visible bg-transparent px-2 py-1"
    >
      <span
        aria-hidden="true"
        className="logo-badge absolute left-1/2 top-[44%] z-0 aspect-square w-[14rem] max-w-[39vw] -translate-x-1/2 -translate-y-1/2 overflow-hidden rounded-full border border-white/70 bg-[radial-gradient(circle_at_42%_36%,rgba(255,255,255,0.98)_0%,rgba(255,255,255,0.82)_24%,rgba(219,235,255,0.55)_48%,rgba(255,255,255,0.18)_70%,rgba(255,255,255,0)_100%)] shadow-[inset_0_2px_8px_rgba(255,255,255,0.95),inset_0_-12px_22px_rgba(11,63,121,0.18),0_5px_16px_rgba(7,26,51,0.3),0_0_26px_rgba(255,255,255,0.48)]"
      />
      <span aria-hidden="true" className="logo-sparkle logo-sparkle-one" />
      <span aria-hidden="true" className="logo-sparkle logo-sparkle-two" />
      <span aria-hidden="true" className="logo-sparkle logo-sparkle-three" />
      <img
        src={logo}
        alt="Maintenant industrial maintenance tracking"
        className="relative z-10 h-full w-full object-contain drop-shadow-[0_12px_30px_rgba(255,255,255,0.24)]"
      />
    </div>
  )
}
