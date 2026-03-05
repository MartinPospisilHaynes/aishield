// Reusable FAQPage JSON-LD komponent pro blog články a stránky
// Generuje schema.org FAQPage structured data pro Google rich snippets

interface FaqItem {
    question: string;
    answer: string;
}

interface FaqJsonLdProps {
    items: FaqItem[];
}

export default function FaqJsonLd({ items }: FaqJsonLdProps) {
    const schema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        mainEntity: items.map((item) => ({
            "@type": "Question",
            name: item.question,
            acceptedAnswer: {
                "@type": "Answer",
                text: item.answer,
            },
        })),
    };

    return (
        <script
            type="application/ld+json"
            dangerouslySetInnerHTML={{ __html: JSON.stringify(schema) }}
        />
    );
}
