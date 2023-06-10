import {
  Container,
  Divider,
  Heading,
  HStack,
  Icon,
  Link,
  VStack,
} from "@chakra-ui/react";
import Card from "common/components/Card";
import PageHeader from "common/components/PageHeader";
import { Fragment } from "react";
import { FiArrowRight } from "react-icons/fi";
import { Link as RouterLink } from "react-router-dom";

const SETTINGS = [
  {
    title: "Profile Information",
    subSection: [
      {
        title: "Edit name, location, work, purpose",
        route: "account-details",
      },
    ],
  },
  {
    title: "Security",
    subSection: [
      {
        title: "Email address",
        route: "email",
      },
      {
        title: "Change password",
        route: "password",
      },
    ],
  },
];

const Settings = () => {
  return (
    <VStack py={100}>
      <PageHeader
        subTitle={"Account"}
        title={"Settings"}
        desc={"Change your email, password, or account details"}
        stackProps={{ mb: 10 }}
      />
      <Container>
        <VStack spacing={10} w="100%">
          {SETTINGS.map((section) => (
            <Card
              key={section.title}
              boxProps={{ borderRadius: "md", w: "100%" }}
            >
              <VStack p={5} align="flex-start">
                <Heading size="md">{section.title}</Heading>
                {section.subSection.map((subSection, index) => (
                  <Fragment key={subSection.title}>
                    <Link
                      as={RouterLink}
                      w="100%"
                      py={3}
                      style={{ textDecoration: "none" }}
                      to={`/settings/${subSection.route}`}
                    >
                      <HStack w="100%" justify="space-between">
                        <Heading size="sm" fontWeight={500}>
                          {subSection.title}
                        </Heading>
                        <Icon as={FiArrowRight} />
                      </HStack>
                    </Link>
                    {index < section.subSection.length - 1 && <Divider />}
                  </Fragment>
                ))}
              </VStack>
            </Card>
          ))}
        </VStack>
      </Container>
    </VStack>
  );
};

export default Settings;
