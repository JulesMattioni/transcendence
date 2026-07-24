import LegalPage from "./LegalPage";

/** Titled section wrapper for a block of legal content. */
function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section>
      <h2 className="mb-3 font-sans text-xl font-semibold text-gray-900">{title}</h2>
      <div className="space-y-3">{children}</div>
    </section>
  );
}

/** Privacy policy page rendered inside the shared legal layout. */
function PrivacyPolicyPage() {
  return (
    <LegalPage title="Privacy Policy" lastUpdated="July 21, 2026">
      <p>
        This Privacy Policy explains how <strong>Keepr</strong> ("we", "us", the
        "Service") collects, uses, stores and protects your personal data when
        you use our secure document management and AI assistant platform. We are
        committed to processing your data lawfully, transparently and only for
        the purposes described below.
      </p>

      <Section title="1. Data We Collect">
        <p>We collect only the data necessary to operate the Service:</p>
        <ul className="list-disc space-y-2 pl-6">
          <li>
            <strong>Account data:</strong> first name, last name, email address
            and an encrypted (hashed) password when you register.
          </li>
          <li>
            <strong>Authentication data:</strong> two-factor authentication (2FA)
            secrets, and identifiers provided by third-party sign-in providers
            (Google, 42) if you choose to use OAuth login.
          </li>
          <li>
            <strong>Documents you upload:</strong> files you store in your
            organisation's vault, along with their metadata (name, size, type,
            upload date, owner).
          </li>
          <li>
            <strong>Usage &amp; audit data:</strong> actions performed within an
            organisation (uploads, access, role changes) recorded in the audit
            log for security purposes.
          </li>
          <li>
            <strong>AI assistant data:</strong> the questions you send to the
            chat assistant and the documents it references to answer them.
          </li>
          <li>
            <strong>Technical data:</strong> session tokens and basic connection
            metadata required to keep you securely signed in.
          </li>
        </ul>
      </Section>

      <Section title="2. How We Use Your Data">
        <ul className="list-disc space-y-2 pl-6">
          <li>To create and manage your account and authenticate you securely.</li>
          <li>To store, organise and let you retrieve your documents.</li>
          <li>To power the AI assistant that answers questions about your documents.</li>
          <li>To enforce role-based access control within your organisation.</li>
          <li>To maintain an audit trail and detect suspicious or unauthorised activity.</li>
          <li>To comply with our legal obligations.</li>
        </ul>
        <p>
          We do <strong>not</strong> sell your personal data, and we do not use
          your documents to train third-party AI models.
        </p>
      </Section>

      <Section title="3. Legal Basis for Processing">
        <p>
          We process your data on the basis of the performance of our contract
          with you (providing the Service), your consent (for optional features
          such as OAuth login), and our legitimate interest in keeping the
          platform secure.
        </p>
      </Section>

      <Section title="4. Data Storage &amp; Security">
        <p>
          Passwords are stored using strong one-way hashing and are never kept in
          plain text. Access to the platform is protected by authentication,
          optional two-factor authentication, and a web application firewall.
          Documents are stored within your organisation's isolated space and are
          only accessible to authorised members.
        </p>
      </Section>

      <Section title="5. Data Sharing">
        <p>
          Your data is only accessible to members of your own organisation
          according to their role. We share data with third parties solely when
          you actively use an integration (e.g. Google or 42 for sign-in) or
          where required by law. We never share your documents publicly.
        </p>
      </Section>

      <Section title="6. Data Retention">
        <p>
          We retain your personal data and documents for as long as your account
          remains active. When you delete your account, your personal data and
          documents are removed, except where we are legally required to retain
          certain records (such as security audit logs) for a limited period.
        </p>
      </Section>

      <Section title="7. Your Rights">
        <p>
          Depending on your jurisdiction (including under the GDPR), you have the
          right to access, correct, export or delete your personal data, to
          restrict or object to certain processing, and to withdraw consent at
          any time. To exercise these rights, contact us using the details below.
        </p>
      </Section>

      <Section title="8. Cookies &amp; Local Storage">
        <p>
          We use browser local storage to keep your session tokens so you stay
          signed in. These are strictly necessary for the Service to function and
          are not used for advertising or tracking.
        </p>
      </Section>

      <Section title="9. Changes to This Policy">
        <p>
          We may update this Privacy Policy from time to time. Any changes will
          be posted on this page with an updated revision date.
        </p>
      </Section>

      <Section title="10. Contact">
        <p>
          For any question regarding this Privacy Policy or your personal data,
          please contact us at{" "}
          <a className="text-keepr underline" href="mailto:privacy@keepr.local">
            privacy@keepr.local
          </a>
          .
        </p>
      </Section>
    </LegalPage>
  );
}

export default PrivacyPolicyPage;
