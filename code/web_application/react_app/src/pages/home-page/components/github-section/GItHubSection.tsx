import { Container } from "@chakra-ui/react";
import FeatureGridLayout from "../blocks/feature-text-image/FeatureGridLayout";
import FeatureImage from "../blocks/feature-text-image/FeatureImage";
import FeatureText from "../blocks/feature-text-image/FeatureText";
import GitHubImage from "./GitHubImage";

const GitHubSection = () => {
  return (
    <Container maxW={"5xl"} py={20}>
      <FeatureGridLayout>
        <FeatureText
          left={true}
          head={"Open-source forever."}
          desc={
            "We're open-source, so check out our project on GitHub. Your contributions are welcomed."
          }
          link="https://github.com/deskool/brainworks-public"
          linkPrompt="Check out our GitHub"
        />
        <FeatureImage image={<GitHubImage />} />
      </FeatureGridLayout>
    </Container>
  );
};

export default GitHubSection;
