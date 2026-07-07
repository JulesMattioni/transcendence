function DiscoverSection() {
  return (
    <section className="px-6 py-20 sm:px-10">
      <div className="flex flex-col gap-8 lg:flex-row lg:items-center">
        {/* left column */}
        <div className="lg:w-2/3">
          <h2 className="font-serif text-4xl leading-tight font-bold text-ink sm:text-5xl">
            Discover a new way to access your data.
          </h2>
          <p className="mt-6 font-sans text-lg text-muted sm:text-xl">
            <span className="font-semibold text-ink">Upload files</span> to your
            organisation and access them by chatting with our chatbot. You will
            never have to read endless documents by yourself, our{' '}
            <span className="font-semibold text-ink">RAG</span> system will
            display the{' '}
            <span className="font-semibold text-ink">right informations</span>{' '}
            for you.
          </p>
        </div>

        {/* right column */}
        <div className="flex shrink-0 justify-center lg:w-1/3">
          <a
            href="#"
            className="inline-block bg-keepr px-8 py-3 text-sm font-sans font-semibold text-white transition-colors hover:bg-blue-700"
          >
            Try Now
          </a>
        </div>
      </div>
    </section>
  )
}

export default DiscoverSection
