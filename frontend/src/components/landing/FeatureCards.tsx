import angel1 from '../../assets/angel_1.png'
import angel2 from '../../assets/angel_2.png'
import angel3 from '../../assets/angel_3.png'

const cards = [
  {
    image: angel1,
    title: 'Data Safety',
    text: 'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod  tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim  veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea  commodo consequat. Duis aute irure dolor in reprehenderit in voluptate  velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint  occaecat cupidatat non proident, sunt in culpa qui officia deserunt  mollit anim id est laborum.',
  },
  {
    image: angel2,
    title: 'Role-based Permissions',
    text: 'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod  tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim  veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea  commodo consequat. Duis aute irure dolor in reprehenderit in voluptate  velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint  occaecat cupidatat non proident, sunt in culpa qui officia deserunt  mollit anim id est laborum.',
  },
  {
    image: angel3,
    title: 'Smart Access',
    text: 'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod  tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim  veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea  commodo consequat. Duis aute irure dolor in reprehenderit in voluptate  velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint  occaecat cupidatat non proident, sunt in culpa qui officia deserunt  mollit anim id est laborum.',
  },
]

function FeatureCards() {
  return (
    <section className="px-6 py-20 sm:px-10">
      <div className="grid grid-cols-1 gap-8 md:grid-cols-3">
        {cards.map((card) => (
          <div key={card.title} className="group border border-gray-200 p-4 bg-white transition-colors duration-300 hover:border-keepr">
            {/* Box */}
            <div className="relative aspect-[3/2] w-full overflow-hidden bg-white transition-colors duration-300 group-hover:bg-keepr">
              {/* White angel */}
              <img
                src={card.image}
                alt=""
                className="h-full w-full scale-150 select-none object-cover opacity-0 object-top mix-blend-screen transition-opacity duration-300 group-hover:opacity-100"
              />
              {/* Blue angel */}
              <div
                aria-hidden
                className="absolute inset-0 scale-150 bg-keepr opacity-100 transition-opacity duration-300 group-hover:opacity-0"
                style={{
                  maskImage: `url(${card.image})`,
                  WebkitMaskImage: `url(${card.image})`,
                  maskSize: 'cover',
                  WebkitMaskSize: 'cover',
                  maskPosition: 'top',
                  WebkitMaskPosition: 'top',
                }}
              />
            </div>
            {/* Title */}
            <h3 className="mt-6 font-serif text-2xl font-bold text-ink">
              {card.title}
            </h3>
            {/* Text */}
            <p className="mt-3 font-sans text-sm leading-relaxed text-muted">
              {card.text}
            </p>
          </div>
        ))}
      </div>
    </section>
  )
}

export default FeatureCards
