// Forwards Endive's shared and personal addresses to the founders' Gmail, and never loses a message:
// 1. every message is saved to the private R2 bucket `endive-mail-archive` before anything else (inbox/...);
// 2. it is forwarded to each person it is for;
// 3. if Gmail refuses a forward (it does, with "421 4.7.28 unusual rate of unsolicited mail", for mail from Google),
//    the message is copied to failed/... and a fresh "Missed email" message with the original attached is sent instead.
// Archived .eml files open in Outlook, Apple Mail or Thunderbird; download them from the R2 bucket in the dashboard.

const MARK = "markturley123@gmail.com";
const TOM = "thomaspaulharan@gmail.com";

// Who each address goes to. A "+tag" (mark+xero@endive.ie) goes where the address without it goes.
const ROUTES = {
  "mark@endive.ie": [MARK],
  "admin@endive.ie": [MARK, TOM],
  "dev@endive.ie": [MARK, TOM],
  "hello@endive.ie": [MARK, TOM],
  "hello@softspotgifts.com": [MARK, TOM],
};
const DEFAULT_ROUTE = [MARK, TOM];

const RESCUE_FROM = "mail-rescue@endive.ie";

function baseAddress(address) {
  const [local, domain] = address.toLowerCase().split("@");
  return `${local.split("+")[0]}@${domain}`;
}

function archiveKey(prefix, to, when) {
  const iso = when.toISOString();
  const day = iso.slice(0, 10).replaceAll("-", "/");
  const id = crypto.randomUUID().slice(0, 8);
  return `${prefix}/${day}/${baseAddress(to)}/${iso.replaceAll(":", "-")}-${id}.eml`;
}

function cleanHeader(value, max = 200) {
  return (value || "").replace(/[\r\n]+/g, " ").slice(0, max);
}

function toBase64(bytes) {
  let binary = "";
  const chunk = 0x8000;
  for (let i = 0; i < bytes.length; i += chunk) {
    binary += String.fromCharCode(...bytes.subarray(i, i + chunk));
  }
  return btoa(binary);
}

export default {
  async email(message, env) {
    const when = new Date();
    const subject = cleanHeader(message.headers.get("subject"));
    const meta = { from: cleanHeader(message.from), to: cleanHeader(message.to), subject };
    const raw = new Uint8Array(await new Response(message.raw).arrayBuffer());

    // 1. Save first, so nothing below can lose it.
    let archived = null;
    try {
      archived = archiveKey("inbox", message.to, when);
      await env.ARCHIVE.put(archived, raw, {
        httpMetadata: { contentType: "message/rfc822" },
        customMetadata: meta,
      });
    } catch (err) {
      archived = null;
      console.error("archive failed", err?.message);
    }

    // 2. Forward.
    const recipients = ROUTES[baseAddress(message.to)] ?? DEFAULT_ROUTE;
    const results = await Promise.allSettled(recipients.map((to) => message.forward(to)));
    const failed = recipients.filter((_, i) => results[i].status === "rejected");
    if (failed.length === 0) return;

    const reasons = results
      .filter((r) => r.status === "rejected")
      .map((r) => cleanHeader(r.reason?.message, 300));
    console.error("forward failed", JSON.stringify({ ...meta, failed, reasons }));

    // 3. Keep a copy where failures are easy to find, then try a fresh message with the original attached.
    try {
      await env.ARCHIVE.put(archiveKey("failed", message.to, when), raw, {
        httpMetadata: { contentType: "message/rfc822" },
        customMetadata: { ...meta, failed: failed.join(","), reason: reasons.join(" | ").slice(0, 500) },
      });
    } catch (err) {
      console.error("failed-copy archive failed", err?.message);
    }

    const rescued = [];
    for (const to of failed) {
      try {
        await env.EMAIL.send({
          to,
          from: RESCUE_FROM,
          subject: `Missed email: ${subject || "(no subject)"}`,
          text:
            `Gmail refused the forward of an email to ${message.to}, so here it is as an attachment.\n\n` +
            `From: ${meta.from}\nTo: ${meta.to}\nSubject: ${subject}\nReceived: ${when.toISOString()}\n\n` +
            `Open the attached .eml to read it. A copy is also kept in Cloudflare R2, bucket endive-mail-archive` +
            (archived ? `, at ${archived}.` : "."),
          attachments: [
            {
              filename: "original.eml",
              type: "message/rfc822",
              disposition: "attachment",
              content: toBase64(raw),
            },
          ],
        });
        rescued.push(to);
      } catch (err) {
        console.error("rescue send failed", to, err?.code, err?.message);
      }
    }

    // Only bounce back to the sender if nobody got it in any form and it is not saved either.
    if (failed.length === recipients.length && rescued.length === 0 && !archived) {
      message.setReject("Delivery failed, please try again later.");
    }
  },
};
