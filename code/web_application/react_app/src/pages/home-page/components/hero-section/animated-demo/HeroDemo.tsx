import { Box, Center, Container, useMediaQuery } from "@chakra-ui/react";

import { gray300 } from "../../../../../setup/theme/colors";

const HeroDemo2 = () => {
  const [isSmallerThan500] = useMediaQuery("(max-width: 500px)");

  return (
    <Container maxW="3xl">
      <Center>
        <Box
          m={"auto"}
          border="1px"
          borderColor={gray300}
          p={5}
          boxShadow="md"
          bg={"white"}
          zIndex={1}
          w="100%"
          h={{ base: "200px", sm: "400px" }}
        >
          <video
            style={{ width: "100%", height: "100%" }}
            muted
            autoPlay
            loop
            controls={isSmallerThan500}
          >
            <source src={"/videos/herodemovideo.mp4"} type="video/mp4" />
          </video>
        </Box>
      </Center>
    </Container>
  );
};

export default HeroDemo2;
