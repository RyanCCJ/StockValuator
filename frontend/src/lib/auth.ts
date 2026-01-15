import NextAuth, { NextAuthConfig } from "next-auth";
import Google from "next-auth/providers/google";
import Credentials from "next-auth/providers/credentials";

const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

// Build providers list - only include Google if credentials are configured
const providers: NextAuthConfig["providers"] = [];

if (process.env.GOOGLE_CLIENT_ID && process.env.GOOGLE_CLIENT_SECRET) {
    providers.push(
        Google({
            clientId: process.env.GOOGLE_CLIENT_ID,
            clientSecret: process.env.GOOGLE_CLIENT_SECRET,
        })
    );
}

providers.push(
    Credentials({
        name: "credentials",
        credentials: {
            email: { label: "Email", type: "email" },
            password: { label: "Password", type: "password" },
        },
        async authorize(credentials) {
            if (!credentials?.email || !credentials?.password) {
                return null;
            }

            try {
                const response = await fetch(`${backendUrl}/auth/login`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        email: credentials.email,
                        password: credentials.password,
                    }),
                });

                if (!response.ok) {
                    return null;
                }

                const data = await response.json();
                return {
                    id: credentials.email as string,
                    email: credentials.email as string,
                    accessToken: data.access_token,
                };
            } catch {
                return null;
            }
        },
    })
);

export const { handlers, signIn, signOut, auth } = NextAuth({
    providers,
    callbacks: {
        async jwt({ token, user, account, profile }) {
            // For Google OAuth, exchange Google auth for backend JWT
            if (account?.provider === "google" && profile?.email) {
                try {
                    const response = await fetch(`${backendUrl}/auth/google`, {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({
                            email: profile.email,
                            google_id: account.providerAccountId,
                        }),
                    });

                    if (response.ok) {
                        const data = await response.json();
                        token.accessToken = data.access_token;
                    }
                } catch (error) {
                    console.error("Failed to exchange Google token:", error);
                }
            }

            // For credentials login, token already has accessToken from authorize
            if (user) {
                const userWithToken = user as { accessToken?: string };
                if (userWithToken.accessToken) {
                    token.accessToken = userWithToken.accessToken;
                }
            }

            return token;
        },
        async session({ session, token }) {
            if (token.accessToken) {
                (session as { accessToken?: string }).accessToken = token.accessToken as string;
            }
            return session;
        },
    },
    pages: {
        signIn: "/login",
    },
});
