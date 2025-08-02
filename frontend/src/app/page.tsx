import { Button } from "@/components/ui/button"
import Link from "next/link";

export default function Home() {

  return (
    <div className="h-screen bg-[#EFEDE8]">
      {/* Header */}
      <header className="flex items-center justify-between mx-8 md:mx-20 h-[10vh] border-b border-[#D9D9D9]">
        <div className="flex items-center space-x-2">
          <img src={'/logo.png'} className="md:w-[60px] md:h-[60px] w-[40px] h-[40px]" />
          <h1 className="text-xl font-satoshi md:text-3xl font-bold text-black">NaviMed</h1>
        </div>

        <Link href="/appointment">     
          <Button className="cursor-pointer">
            Book an Appointment
          </Button>
        </Link>
      </header>

      {/* Main Content */}
      <main className="flex flex-col lg:flex-row h-[90vh] py-8 w-full mx-8 md:mx-20">
        {/* Left Content */}
        <div className="w-[84%] lg:w-[55%] h-[40%] lg:h-full flex flex-col justify-center">
          {/* <p className="text-gray-600 mb-3 md:mb-4 text-sm md:text-base">World&apos;s Most Adopted Healthcare AI</p> */}
          
          <h2 className="text-3xl sm:text-4xl md:text-5xl lg:text-7xl font-medium font-satoshi text-black mb-4 md:mb-6 leading-tight">
            Revolutionizing<br />
            Healthcare with AI
          </h2>
          
          <p className="text-gray-600 text-base md:text-lg mb-6 md:mb-8 max-w-lg mx-auto lg:mx-0">
            We use advanced reinforcement learning algorithms to optimize patient queue in real-time for maximum efficiency 
          </p>
          
          <div className="flex flex-col sm:flex-row gap-3 md:gap-4 mb-8 md:mb-12 justify-center lg:justify-start">
            <Link href="/appointment">
              <Button size={'lg'} className="text-[16px] cursor-pointer">
                Book an Appointment
              </Button>
            </Link>
          </div>
        </div>

        {/* Right Content - Robot Image and Stats */}
        <div className="w-[75%] ml-[10%] md:ml-[1%] lg:w-[35%] h-[60%] lg:h-full relative flex flex-col justify-end">
              <img
                src="/robot.png"
                alt="Healthcare AI Robot"
                className="object-fill"
              />
            
        </div>
      </main>
    </div>
  )
}