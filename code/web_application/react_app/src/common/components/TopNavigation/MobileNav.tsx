import {
  Drawer,
  DrawerBody,
  DrawerCloseButton,
  DrawerContent,
  DrawerHeader,
  DrawerOverlay,
  VStack,
} from "@chakra-ui/react";
import { Link } from "react-router-dom";
import LogoWithText from "../LogoWithText";
import NavRoutes from "./NavRoutes";

interface AppProps {
  isOpen: boolean;
  onClose: () => void;
}

const MobileNav = ({ isOpen, onClose }: AppProps) => {
  return (
    <Drawer isOpen={isOpen} placement="right" onClose={onClose}>
      <DrawerOverlay />
      <DrawerContent>
        <DrawerCloseButton />
        <DrawerHeader>
          <Link to="/">
            <LogoWithText />
          </Link>
        </DrawerHeader>
        <DrawerBody>
          <VStack w="100%" align="flex-start" spacing={5}>
            <NavRoutes />
          </VStack>
        </DrawerBody>
      </DrawerContent>
    </Drawer>
  );
};

export default MobileNav;
