import {
  Box,
  Divider,
  Flex,
  IconButton,
  Stack,
  useDisclosure,
  useMediaQuery,
} from "@chakra-ui/react";
import { FiMenu } from "react-icons/fi";
import { Link } from "react-router-dom";
import LogoWithText from "../LogoWithText";
import MobileNav from "./MobileNav";
import NavRoutes from "./NavRoutes";

const Navigation = () => {
  const { isOpen, onOpen, onClose } = useDisclosure();
  const [isSmallerThan500] = useMediaQuery("(max-width: 500px)");
  return (
    <Box
      position={"static"}
      bg="white"
      w={"100%"}
      h={"6vh"}
      zIndex={1000}
      as="header"
    >
      <Flex
        pr={7}
        pl={4}
        h={"100%"}
        alignItems={"center"}
        justifyContent={"space-between"}
      >
        <Box>
          <Link to="/">
            <LogoWithText />
          </Link>
        </Box>
        <Flex alignItems={"center"}>
          <Stack align="center" direction={"row"} spacing={7}>
            {isSmallerThan500 ? (
              <>
                <IconButton
                  variant="outline"
                  onClick={onOpen}
                  aria-label="open menu"
                  icon={<FiMenu />}
                />
                <MobileNav onClose={onClose} isOpen={isOpen} />
              </>
            ) : (
              <NavRoutes />
            )}
          </Stack>
        </Flex>
      </Flex>
      <Divider />
    </Box>
  );
};
export default Navigation;
