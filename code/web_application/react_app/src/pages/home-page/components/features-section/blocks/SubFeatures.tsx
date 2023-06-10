import { ExternalLinkIcon } from "@chakra-ui/icons";
import { Flex, HStack, Icon, Link, Text, VStack } from "@chakra-ui/react";

import { brand100 } from "../../../../../setup/theme/colors";
import { FeatureItemType } from "./Feature";

interface FeatureItemProps {
  feature: FeatureItemType;
  setSubFeatureState?: React.Dispatch<React.SetStateAction<number>>;
  subFeatureState?: number;
  setStop?: React.Dispatch<React.SetStateAction<boolean>>;
  index: number;
}

const FeatureItem = ({
  feature,
  setSubFeatureState,
  subFeatureState,
  index,
  setStop,
}: FeatureItemProps) => {
  const { icon, link, text } = feature;

  const handleFeatureItemClick = () => {
    if (setSubFeatureState) {
      setSubFeatureState(index);
    }
    if (setStop) {
      setStop(true);
    }
  };

  return (
    <HStack
      spacing={3}
      onClick={handleFeatureItemClick}
      bg={subFeatureState === index ? brand100 : ""}
      p={2}
      borderRadius="10px"
    >
      <Flex
        justify={"center"}
        align={"center"}
        w={{ base: 35, sm: 50 }}
        h={{ base: 30, sm: 50 }}
        bg={"brand"}
        color={"white"}
        rounded={"md"}
        fontSize={{ base: 20, sm: 32 }}
        boxShadow={"md"}
      >
        {icon}
      </Flex>
      {link ? (
        <Link w={{ base: "100%", sm: "250px" }} href={link} isExternal>
          <Text fontSize={{ base: "xs", sm: "sm" }}>
            {text} <Icon as={ExternalLinkIcon} mb={1} />
          </Text>
        </Link>
      ) : (
        <Text
          fontSize={{ base: "xs", sm: "sm" }}
          w={{ base: "100%", sm: "250px" }}
        >
          {text}
        </Text>
      )}
    </HStack>
  );
};

interface AppProps {
  features: FeatureItemType[];
  setSubFeatureState?: React.Dispatch<React.SetStateAction<number>>;
  subFeatureState?: number;
  setStop?: React.Dispatch<React.SetStateAction<boolean>>;
}

const SubFeatures = ({
  features,
  setSubFeatureState,
  subFeatureState,
  setStop,
}: AppProps) => {
  return (
    <VStack spacing={3} w={{ base: "100%", md: "auto" }}>
      {features.map((item, ind) => (
        <FeatureItem
          setSubFeatureState={setSubFeatureState}
          subFeatureState={subFeatureState}
          key={item.text}
          feature={item}
          setStop={setStop}
          index={ind}
        />
      ))}
    </VStack>
  );
};

export default SubFeatures;
