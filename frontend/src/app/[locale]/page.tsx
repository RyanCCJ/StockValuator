import { redirect } from "@/i18n/routing";
import { auth } from "@/lib/auth";

export default async function Home() {
  const session = await auth();

  if (session) {
    redirect({ href: "/dashboard", locale: "en" });
  } else {
    redirect({ href: "/login", locale: "en" });
  }
}
