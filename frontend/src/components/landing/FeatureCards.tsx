import angel1 from "../../assets/angel_1.png";
import angel2 from "../../assets/angel_2.png";
import angel3 from "../../assets/angel_3.png";

const cards = [
  {
    image: angel1,
    title: "Data Safety",
    text: "Your documents are encrypted and stored in isolated organisation vaults, kept fully separate from every other team. Every action — uploads, edits, downloads and deletions — is captured in a real-time audit log, so you always know exactly who touched what, and when. Nothing happens to your files without leaving a trace.",
  },
  {
    image: angel2,
    title: "Role-based Permissions",
    text: "Grant each member the right level of access — admin, editor or reader — and control exactly who can view, upload or manage files. Invite teammates to your organisation, adjust their roles as your team evolves, and revoke access in a single click. Sensitive documents stay in the hands of the people who should see them.",
  },
  {
    image: angel3,
    title: "Smart Access",
    text: "Ask questions in plain language and let our AI assistant answer straight from your documents, with citations pointing back to the exact sources. It respects every permission boundary, so it never surfaces information a user isn't cleared to see — turning hours of manual searching into a simple conversation.",
  },
];

function FeatureCards() {
  return (
    <section className="px-6 py-20 sm:px-10">
      <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
        {cards.map((card) => (
          <div
            key={card.title}
            className="group rounded p-4 bg-white shadow-sm ring-1 ring-transparent transition-shadow duration-300 hover:shadow-md hover:ring-keepr"
          >
            {/* Box */}
            <div className="relative aspect-[3/2] w-full overflow-hidden rounded bg-white transition-colors duration-300 group-hover:bg-keepr">
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
                  maskSize: "cover",
                  WebkitMaskSize: "cover",
                  maskPosition: "top",
                  WebkitMaskPosition: "top",
                }}
              />
            </div>
            {/* Title */}
            <h3 className="mt-6 font-serif text-2xl font-bold text-black">
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
  );
}

export default FeatureCards;
