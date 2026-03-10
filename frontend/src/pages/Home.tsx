import { Code, Image, RocketIcon, User } from "lucide-react";
import { Link } from "react-router";
import { Button } from "~/components/ui/button";

import { CardImage } from "~/components/CardImage";
import Waves from "~/components/Waves";
import Dither from "~/components/Dither";
import GridMotion from "~/components/GridMotion";
import { useAppContext } from "~/context/useAppContext";

const session = false; // TODO: Replace with actual session check

export default function Home() {
  const { theme } = useAppContext();

  return (
    <main className="flex flex-col items-center justify-between">
      <div className="flex min-h-[calc(100vh-var(--header-height,4rem))] w-full flex-col items-center justify-between gap-16">
        <div className="flex w-full flex-col items-center gap-4 px-6 pt-16">
          <div className="font-geist text-primary relative flex flex-col items-start text-4xl font-semibold sm:text-5xl md:text-5xl dark:drop-shadow-[0_4px_8px_rgba(0,0,0,0.5)]">
            <span className="relative flex items-center gap-2">
              <span className="relative isolate px-2 py-1">
                {/* Dither canvas behind the text */}
                <span className="animate-in fade-in absolute inset-0 -inset-x-2 -z-10 overflow-hidden duration-1000">
                  <Dither
                    waveColor={
                      theme === "light" ? [0.48, 0.48, 0.48] : [0.32, 0.15, 1]
                    }
                    disableAnimation={false}
                    enableMouseInteraction
                    mouseRadius={0}
                    colorNum={4}
                    pixelSize={1.2}
                    waveAmplitude={0.3}
                    waveFrequency={3}
                    waveSpeed={0.05}
                  />
                </span>

                {/* to invert do: mix-blend-mode */}
                <span className="z-10 text-white select-none">
                  <span>True</span>
                  <span className="">Lens</span>
                </span>
              </span>

              {/* <img
                src={polaroidPohoto}
                alt="Logo Png"
                className="w-12 -rotate-10 rounded-md sm:w-14 md:w-16 dark:brightness-[1] dark:drop-shadow-[0_4px_40px_rgba(255,255,255,0.3)]"
              /> */}
            </span>
          </div>
        </div>

        <div className="relative h-72 w-full sm:h-80 md:h-96">
          <Waves
            lineColor="#5a5a5a"
            backgroundColor="transparent"
            waveSpeedX={0.02}
            waveSpeedY={0.01}
            waveAmpX={40}
            waveAmpY={20}
            friction={0.9}
            tension={0.01}
            maxCursorMove={120}
            xGap={12}
            yGap={36}
          />

          <div className="from-background to-background pointer-events-none absolute inset-0 bg-linear-to-r via-transparent" />

          <div className="absolute inset-0 flex items-center justify-center px-10 sm:px-14 md:px-20">
            <p className="font-space-grotesk text-primary max-w-4xl text-lg font-medium sm:text-2xl md:text-2xl lg:text-3xl">
              Advanced AI detection that verifies media authenticity in real
              time and protects platforms from synthetic content and
              impersonation.
            </p>
          </div>
        </div>

        <div className="my-auto">
          <div className="font-geist mx-auto flex w-fit flex-col items-center px-6 py-8">
            <div className="mx-auto flex w-fit items-center gap-4 font-mono">
              <Link to="/upload-media">
                <Button
                  size={"lg"}
                  className="bg-muted/50 mt-4 cursor-pointer text-lg font-normal shadow-none"
                  variant={"outline"}
                >
                  <Image />
                  Analyze Media
                </Button>
              </Link>

              <Link to="">
                <Button
                  size={"lg"}
                  className="bg-muted/50 mt-4 cursor-pointer text-lg font-normal shadow-none"
                  variant={"outline"}
                >
                  <RocketIcon />
                  Get Started
                </Button>
              </Link>
            </div>

            <Link
              to={session ? "/upload" : "/sign-in?next=/upload"}
              className="w-full"
            >
              {!session ? (
                <Button
                  size={"lg"}
                  className="font-space-grotesk mt-4 w-full cursor-pointer text-lg shadow-none"
                  variant={"default"}
                >
                  <User strokeWidth={3} />
                  Sign in
                </Button>
              ) : (
                <Button
                  size={"lg"}
                  className="font-space-grotesk mt-4 w-full cursor-pointer text-lg shadow-none"
                  variant={"default"}
                >
                  Analyze Media <Code strokeWidth={3} />
                </Button>
              )}
            </Link>
          </div>
        </div>
      </div>

      <div className="to-background w-full bg-linear-to-t from-transparent py-24">
        <div className="relative mx-6 h-96 overflow-hidden rounded-lg sm:mx-8 md:mx-12 lg:mx-16">
          <GridMotion
            gradientColor="#5227FF"
            items={[
              "https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=800&q=80",
              "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=800&q=80",
              "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=800&q=80",
              "https://images.unsplash.com/photo-1531746020798-e6953c6e8e04?w=800&q=80",
              "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=800&q=80",
              "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=800&q=80",
              "https://images.unsplash.com/photo-1552058544-f2b08422138a?w=800&q=80",
              "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=800&q=80",
              "https://images.unsplash.com/photo-1548142813-c348350df52b?w=800&q=80",
              "https://images.unsplash.com/photo-1580489944761-15a19d654956?w=800&q=80",
              "https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=800&q=80",
              "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=800&q=80",
              "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=800&q=80",
              "https://images.unsplash.com/photo-1531746020798-e6953c6e8e04?w=800&q=80",
              "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=800&q=80",
              "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=800&q=80",
              "https://images.unsplash.com/photo-1552058544-f2b08422138a?w=800&q=80",
              "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=800&q=80",
              "https://images.unsplash.com/photo-1548142813-c348350df52b?w=800&q=80",
              "https://images.unsplash.com/photo-1580489944761-15a19d654956?w=800&q=80",
            ]}
          />
        </div>
        <div className="font-geist text-muted-foreground mt-2 text-center text-lg italic">
          Because Every Image Deserves the Truth.
        </div>
      </div>

      <div className="grid w-full grid-cols-1 gap-8 px-6 py-12 sm:px-8 md:grid-cols-3 md:px-12 lg:px-16">
        <CardImage
          imageSrc="https://www.ofcom.org.uk/topic-and-subtopics/online-safety/illegal-and-harmful-content/information-for-industry/deepfake-defences/contentassets/deepfake-adobestock_828798592.jpg"
          disableImageEffect
          imageAlt="AI analyzing media"
          className="w-full max-w-md"
          title="Real-Time Deepfake Detection"
          description="Our AI scans videos and images to instantly detect manipulated media and synthetic content."
          buttonLabel="Try Detection"
          onButtonClick={() => console.log("Try Detection")}
        />

        <CardImage
          imageSrc="https://www.statnews.com/wp-content/uploads/2026/02/AdobeStock_330230890-645x645.jpeg"
          disableImageEffect
          imageAlt="Cyber security analysis"
          className="w-full max-w-md"
          title="AI Media Forensics"
          description="Advanced machine learning analyzes facial artifacts and frame inconsistencies."
          buttonLabel="Learn More"
          onButtonClick={() => console.log("Learn More")}
        />

        <CardImage
          title="Misinformation Protection"
          imageSrc="https://images.unsplash.com/photo-1677442136019-21780ecad995"
          disableImageEffect
          description="Stop the spread of fake media and protect your brand, users, and reputation."
          className="w-full max-w-md"
          buttonLabel="Learn More"
          onButtonClick={() => console.log("Explore")}
        />
      </div>
    </main>
  );
}
