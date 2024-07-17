import { useState } from "react";
import { Button } from "@/components/ui/button";
import YouTubeEmbed from "@/components/YoutubeEmbed";

const Home = () => {
  const [inputState, setInputState] = useState("initial");
  const [email, setEmail] = useState("");
  const [inputValue, setInputValue] = useState("");

  const handleButtonClick = () => {
    setInputState("active");
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const response = await fetch('/api/saveData', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email }),
      });

      if (!response.ok) {
        throw new Error('Network response was not ok');
      }

      setInputState("submitted");
    } catch (error) {
      console.error('Error:', error);
      // Handle error (e.g., show error message to user)
    }
  };

  return (
    <div className="dark bg-black text-white min-h-screen flex flex-col items-center justify-center relative overflow-hidden">

      <div className="absolute top-0 -left-4 w-96 h-96 bg-[#90637e] rounded-full mix-blend-screen filter blur-3xl opacity-60 animate-blob z-0"></div>
      <div className="absolute top-0 -right-4 w-96 h-96 bg-zinc-800 rounded-full mix-blend-screen filter blur-xl opacity-100 animate-blob animation-delay-2000 z-0"></div>
      <div className="absolute -bottom-8 left-20 w-96 h-96 bg-[#5e3e51] rounded-full mix-blend-screen filter blur-xl opacity-70 animate-blob animation-delay-4000 z-0"></div>
      
      <div className="absolute inset-0 bg-[url('/bg.png')] bg-cover bg-center opacity-80" />
      <div className="container max-w-3xl px-8 py-2 md:py-2 space-y-8 text-center relative z-20">
        <div className="space-y-4">
          <form onSubmit={handleSubmit} className="flex justify-center">
            {inputState === "active" ? (
              <input
              type="email"
              value={email}
              onChange={(e) => {
                setEmail(e.target.value);
                setInputValue(e.target.value);
              }}
              placeholder="Enter your email"
              className="shadow-[#2b1d25] shadow-2xl bg-gradient-to-tl from-zinc-900 to-zinc-950 text-white placeholder:text-zinc-400 px-0 text-center py-3 rounded-3xl text-sm outline-none focus:ring-1 focus:ring-zinc-900 font-semibold w-full max-w-[400px] transition-all duration-200"
              style={{
                width: `${Math.min(Math.max(inputValue.length * 10, 160), 400)}px`,
              }}
              autoFocus
            />
            ) : inputState === "initial" ? (
          <Button
            type="button"
            onClick={handleButtonClick}
            className="shadow-[#2d1e27] shadow-2xl outline-none ring-0 bg-gradient-to-br from-zinc-950 to-zinc-900 text-zinc-400 px-8 py-3 rounded-3xl text-sm font-semibold focus:shadow-2xl focus:outline-none focus:ring-0"
          >
            Get Early Access
          </Button>
            ) : (
              <div className="bg-zinc-950 text-zinc-400 px-8 py-3 rounded-3xl text-sm font-semibold">
                Thanks! We&apos;ll keep you posted.
              </div>
            )}
          </form>
          
          <h1 className={`text-4xl md:text-6xl font-bold tracking-tight font-heading`}>SampleBox</h1>
          <div className="flex flex-col gap-0 items-center">
            <p className="text-lg md:text-xl text-muted-foreground font-body">
              drop a song and get a sample box.
            </p>
            <p className="text-lg md:text-xl text-zinc-400 font-body">
              includes stems, drums, loops and wonky ideas made from
              that song.
            </p>
          </div>
        </div>

        <YouTubeEmbed embedUrl="https://www.youtube.com/embed/QCLmfS77B3I?si=msjU71YW6YuT_L6q" />
      </div>
    </div>
  );
};

export default Home;