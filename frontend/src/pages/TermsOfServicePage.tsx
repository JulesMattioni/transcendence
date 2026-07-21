import LegalPage from "./LegalPage";

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section>
      <h2 className="mb-3 font-sans text-xl font-semibold text-gray-900">{title}</h2>
      <div className="space-y-3">{children}</div>
    </section>
  );
}

function TermsOfServicePage() {
  return (
    <LegalPage title="Terms of Service" lastUpdated="July 21, 2026">
      <p>
        These Terms of Service ("Terms") govern your access to and use of{" "}
        <strong>Keepr</strong> (the "Service"), a secure document management
        platform with an integrated AI assistant. By creating an account or using
        the Service, you agree to be bound by these Terms.
      </p>

      <Section title="1. Eligibility &amp; Accounts">
        <p>
          You must provide accurate information when registering and are
          responsible for keeping your credentials confidential. You are
          responsible for all activity that occurs under your account. We
          strongly recommend enabling two-factor authentication.
        </p>
      </Section>

      <Section title="2. Acceptable Use">
        <p>You agree not to use the Service to:</p>
        <ul className="list-disc space-y-2 pl-6">
          <li>Upload or share content that is illegal, infringing or malicious.</li>
          <li>Attempt to access data or organisations you are not authorised to access.</li>
          <li>Disrupt, overload, reverse-engineer or compromise the security of the platform.</li>
          <li>Use the Service to store content on behalf of others without authorisation.</li>
        </ul>
      </Section>

      <Section title="3. Your Content">
        <p>
          You retain all rights to the documents you upload. You grant us only
          the limited permission necessary to store, process and display your
          documents and to let the AI assistant reference them when answering
          your questions. You are solely responsible for the content you upload
          and for having the right to store it.
        </p>
      </Section>

      <Section title="4. Organisations &amp; Roles">
        <p>
          Documents are managed within organisations, and access is governed by
          role-based permissions. Organisation administrators may manage members,
          roles and access to documents. You agree to respect the access rules
          set within your organisation.
        </p>
      </Section>

      <Section title="5. AI Assistant">
        <p>
          The AI assistant generates answers based on the documents available to
          you. Its responses may contain errors or omissions and are provided for
          convenience only. You should not rely on them as professional, legal or
          financial advice, and you remain responsible for verifying important
          information.
        </p>
      </Section>

      <Section title="6. Availability">
        <p>
          The Service is provided on an "as available" basis. We may modify,
          suspend or discontinue features at any time. This is an academic
          project, and continuous availability is not guaranteed.
        </p>
      </Section>

      <Section title="7. Termination">
        <p>
          You may stop using the Service and delete your account at any time. We
          may suspend or terminate access if you violate these Terms or use the
          Service in a way that harms other users or the platform.
        </p>
      </Section>

      <Section title="8. Disclaimer &amp; Limitation of Liability">
        <p>
          The Service is provided "as is", without warranties of any kind. To the
          maximum extent permitted by law, we are not liable for any indirect,
          incidental or consequential damages, or for loss of data arising from
          your use of the Service. You are encouraged to keep your own backups of
          important documents.
        </p>
      </Section>

      <Section title="9. Changes to These Terms">
        <p>
          We may update these Terms from time to time. Continued use of the
          Service after changes take effect constitutes acceptance of the revised
          Terms.
        </p>
      </Section>

      <Section title="10. Contact">
        <p>
          For any question about these Terms, please contact us at{" "}
          <a className="text-keepr underline" href="mailto:support@keepr.local">
            support@keepr.local
          </a>
          .
        </p>
      </Section>
    </LegalPage>
  );
}

export default TermsOfServicePage;
