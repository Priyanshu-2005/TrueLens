import { Button } from "~/components/ui/button";
import {
  Card,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "~/components/ui/card";

interface CardImageProps {
  imageSrc?: string;
  imageAlt?: string;
  title?: string;
  description?: string;
  buttonLabel?: string;
  onButtonClick?: () => void;
  className?: string;
  disableImageEffect?: boolean;
  showButton?: boolean;
}

export function CardImage({
  imageSrc = "https://www.ofcom.org.uk/topic-and-subtopics/online-safety/illegal-and-harmful-content/information-for-industry/deepfake-defences/contentassets/deepfake-adobestock_828798592.jpg",
  imageAlt = "Event cover",
  title = "Design systems meetup",
  description = "A practical talk on component APIs, accessibility, and shipping faster.",
  buttonLabel = "View Event",
  onButtonClick,
  className = "",
  disableImageEffect = false,
  showButton = true,
}: CardImageProps) {
  const imageEffectClasses = disableImageEffect
    ? "w-full object-cover"
    : "w-full object-cover brightness-60 grayscale transition-all duration-300 group-hover:brightness-100 group-hover:grayscale-0 dark:brightness-40 dark:group-hover:brightness-75";

  return (
    <Card
    className={`group relative mx-auto w-full overflow-hidden pt-0 flex flex-col h-full ${className}`}
  >
    <img
      src={imageSrc}
      alt={imageAlt}
      className={`relative z-20 aspect-video ${imageEffectClasses}`}
    />
    <CardHeader className="flex-1">
      <CardTitle>{title}</CardTitle>
      <CardDescription>{description}</CardDescription>
    </CardHeader>
    {showButton && (
      <CardFooter className="mt-auto pt-0">
        <Button className="w-full" onClick={onButtonClick}>
          {buttonLabel}
        </Button>
      </CardFooter>
    )}
  </Card>
  );
}
