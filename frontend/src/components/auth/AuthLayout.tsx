import type { ReactNode } from 'react'
import angel4 from '../../assets/angel_4.png'

function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <div className="grid min-h-screen grid-cols-1 lg:grid-cols-2">
      {/* Left column: (desktop only) */}
      <div className="relative hidden overflow-hidden bg-keepr lg:block">
        <div className='items-center px-6 py-5 sm:px-10'>
            <span className="font-sans text-3xl font-bold tracking-tight text-white">
                Keepr.
            </span>
            <h1 className='font-sans py-30 text-6xl font-medium tracking-tight text-white'>
                Discover a new way to access your data.
            </h1>
        </div>
        <img
          src={angel4}
          alt=""
          className="absolute opacity-50 scale-175 top-4/10 inset-0 h-full w-full select-none object-cover mix-blend-screen"
        />
      </div>

      {/* Right column */}
      <div className="flex items-center justify-center px-6 py-12 sm:px-10">
        <div className="w-full max-w-md">{children}</div>
      </div>
    </div>
  )
}

export default AuthLayout
