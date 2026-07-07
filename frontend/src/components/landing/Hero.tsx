import angel0 from '../../assets/angel_0.png'


function Hero() {
  return (
    <section className="relative grid min-h-screen grid-cols-1 content-center items-center gap-8 overflow-hidden px-6 pt-16 pb-16 sm:px-10 lg:min-h-0 lg:grid-cols-2">
      <div className='z-10 overflow-x-hidden pt-8'>
        {/* Badge */}
        <span className="inline-flex items-center gap-2 rounded-full border border-gray-600 px-4 py-1.5 font-mono text-xs text-black-600">
          <span className="h-2 w-2 rounded-full bg-keepr" />
          AI Powered Security Vault
        </span>
        {/* Title */}
        <h1 className="mt-6 font-serif text-5xl leading-tight font-bold text-black sm:text-8xl">
            We keep your documents safe. Access it {''}
            <span className="text-keepr">
                smartly.
            </span>
        </h1>
        {/* Description */}
        <p className="mt-4 font-sans text-lg font-normal text-muted sm:text-xl">
            Role-based {''}
            <span className="font-semibold">permissions govern every file</span>
            , every action is audit-logged  in real time, and an {''}
            <span className="font-semibold">AI assistant </span>
            answers from your documents — {''}
            <span className="font-semibold">never revealing </span>
            what a user isn't cleared to see.
        </p>
        {/* Boutons */}
        <div className="mt-8 flex items-center gap-4">
          <a
            href="#"
            className="bg-keepr px-6 py-3 text-sm font-semibold text-white transition-colors hover:bg-blue-700"
          >
            Get started now
          </a>
          <a
            href="#"
            className="border border-gray-600 bg-white px-6 py-3 text-sm font-semibold text-ink transition-colors hover:bg-gray-50"
          >
            Sign In
          </a>
        </div>

      </div>


      {/* right column */}
      <div className="relative flex justify-center lg:justify-end">
        <img
          src={angel0}
          alt=""
          className="
            absolute top-1/2 left-1/2 w-[150%] max-w-none -translate-x-1/2 -translate-y-5/5 opacity-70 pointer-events-none select-none
            lg:static lg:translate-x-0 lg:translate-y-0 lg:opacity-100 lg:w-full lg:mt-4 lg:scale-125 lg:origin-left
          "
        />
        {/* chat */}
        <div className="absolute top-2/5 left-3/5 hidden w-100 -translate-x-1/2 -translate-y-1/2 border border-keepr bg-white p-4 lg:block">
            <p className="font-mono text-sm text-subtle">
                <span className="animate-blink text-keepr">|</span> Ask anything...
            </p>

          <div className="mt-6 flex items-center justify-between">
            <button className="flex font-sans items-center gap-1 text-xs text-gray-500">
              <span className="text-muted leading-none">+</span> Upload
            </button>
            <button className="flex h-8 w-8 items-center justify-center rounded-full bg-keepr text-white text-lg">
              ↑
            </button>
          </div>
        </div>
      </div>

    </section>
  )
}

export default Hero
