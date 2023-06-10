import { Box, Center, Divider } from "@chakra-ui/react";
import Features from "./components/features-section/FeaturesSection";
import StepsSection from "./components/github-section/GItHubSection";
import HeroSection from "./components/hero-section/HeroSection";
import Footer from "../../common/components/Footer";
import SignUpSection from "./components/signup-section/SignUpSection";
import usePageTitle from "../../common/hooks/usePageTitle";
import AlphaTestingWarning from "common/components/AlphaTestingWarning";

/**
 * Home page
 */
const Home = () => {
  usePageTitle("Home");

  return (
    <>
      <HeroSection />
      <Divider />
      <Center mt={100}>
        <Box maxW="5xl" w="80%">
          <AlphaTestingWarning />
        </Box>
      </Center>
      <Features />
      <StepsSection />
      <SignUpSection />
      <Footer />
    </>
  );
};
export default Home;
