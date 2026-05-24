import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { View, ScrollView, StyleSheet, RefreshControl, Linking } from 'react-native';
import {
  Text,
  Switch,
  Button,
  Card,
  Title,
  Paragraph,
  TextInput,
  Chip,
  ActivityIndicator,
  Divider,
} from 'react-native-paper';
import { deliveryNetwork } from '../services/api';
import { luxuryColors, luxuryTypography } from '../theme/luxuryTheme';

const DeliveryPartnerDashboardScreen = ({ navigation }) => {
  const [profile, setProfile] = useState(null);
  const [inbox, setInbox] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [qrJobId, setQrJobId] = useState('');
  const [qrPayload, setQrPayload] = useState('');
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    try {
      const [me, box] = await Promise.all([deliveryNetwork.partnerMe(), deliveryNetwork.inbox()]);
      setProfile(me.data?.data || me.data);
      setInbox(box.data?.data || box.data || []);
    } catch (e) {
      console.warn('delivery load', e?.message);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const activateProfile = async () => {
    setBusy(true);
    try {
      await deliveryNetwork.partnerRegister({ vehicle_types: ['bike', 'car'], capacity_kg: 120 });
      await load();
    } finally {
      setBusy(false);
    }
  };

  const online = !!profile?.is_online;

  const toggleOnline = async (v) => {
    try {
      await deliveryNetwork.setOnline(v);
      setProfile((p) => ({ ...(p || {}), is_online: v }));
    } catch (e) {
      console.warn('online', e);
    }
  };

  const accept = async (jobId) => {
    setBusy(true);
    try {
      await deliveryNetwork.accept(jobId);
      await load();
    } finally {
      setBusy(false);
    }
  };

  const reject = async (jobId) => {
    setBusy(true);
    try {
      await deliveryNetwork.reject(jobId);
      await load();
    } finally {
      setBusy(false);
    }
  };

  const submitQr = async () => {
    if (!qrJobId.trim() || !qrPayload.trim()) return;
    setBusy(true);
    try {
      await deliveryNetwork.scanQr(qrJobId.trim(), {
        payload_b64: qrPayload.trim(),
        client_ts: Math.floor(Date.now() / 1000),
      });
      setQrPayload('');
      await load();
    } catch (e) {
      console.warn('qr', e);
    } finally {
      setBusy(false);
    }
  };

  const statusLabel = useMemo(() => {
    const s = profile?.status || 'pending';
    return s.charAt(0).toUpperCase() + s.slice(1);
  }, [profile]);

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator color={luxuryColors.champagneGold} />
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.root}
      contentContainerStyle={styles.content}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={luxuryColors.champagneGold} />}
    >
      <Text style={styles.heroKicker}>Shadiro Smart Delivery</Text>
      <Title style={styles.heroTitle}>Partner command center</Title>
      <Paragraph style={styles.heroSub}>Live offers, secure QR pickup, and earnings — built for premium logistics.</Paragraph>

      {(!profile?.vehicle_types || profile.vehicle_types.length === 0) && (
        <Card style={styles.card}>
          <Card.Content>
            <Title style={styles.section}>Activate partner profile</Title>
            <Paragraph style={styles.muted}>Register default bike + car capacity for instant matching (editable later).</Paragraph>
            <Button mode="contained" onPress={activateProfile} loading={busy} style={styles.btnGold}>
              Activate
            </Button>
          </Card.Content>
        </Card>
      )}

      <Card style={styles.card}>
        <Card.Content>
          <View style={styles.rowBetween}>
            <View>
              <Text style={styles.label}>Partner status</Text>
              <Chip style={styles.statusChip} textStyle={styles.statusChipText}>
                {statusLabel}
              </Chip>
            </View>
            <View style={{ alignItems: 'flex-end' }}>
              <Text style={styles.label}>Go online</Text>
              <Switch value={online} onValueChange={toggleOnline} color={luxuryColors.champagneGold} />
            </View>
          </View>
          <Divider style={{ marginVertical: 12 }} />
          <Text style={styles.label}>Wallet (₹)</Text>
          <Text style={styles.wallet}>
            {((profile?.wallet_balance_paise || 0) / 100).toFixed(2)}
          </Text>
          <Text style={styles.muted}>Heatmaps, incentives, and deep analytics ship in the next drop.</Text>
        </Card.Content>
      </Card>

      <Title style={styles.section}>Live requests</Title>
      {inbox.length === 0 ? (
        <Paragraph style={styles.muted}>No active offers. Stay online near pickup zones.</Paragraph>
      ) : (
        inbox.map((row) => (
          <Card key={row.job_id} style={styles.card}>
            <Card.Content>
              <Text style={styles.jobId}>{row.job_id}</Text>
              <Text style={styles.jobLine}>
                {row.pickup_label} → {row.dropoff_label}
              </Text>
              <Text style={styles.muted}>
                {row.item_category} · {row.weight_kg} kg · ETA {row.eta_minutes}m · ₹
                {((row.expected_earnings_paise || 0) / 100).toFixed(0)}
              </Text>
              {row.state === 'assigned' && row.offer_expires_at ? (
                <View style={styles.actions}>
                  <Button mode="contained" onPress={() => accept(row.job_id)} loading={busy} style={styles.btnGold}>
                    Accept
                  </Button>
                  <Button mode="outlined" onPress={() => reject(row.job_id)} disabled={busy}>
                    Reject
                  </Button>
                </View>
              ) : null}
              {row.state !== 'assigned' ? (
                <View style={styles.actions}>
                  <Button
                    mode="contained-tonal"
                    onPress={() => {
                      const addr = row.pickup?.address || row.pickup_label;
                      Linking.openURL(`https://www.google.com/maps/dir/?api=1&destination=${encodeURIComponent(addr)}`);
                    }}
                  >
                    Navigate pickup
                  </Button>
                </View>
              ) : null}
            </Card.Content>
          </Card>
        ))
      )}

      <Title style={styles.section}>Secure QR pickup</Title>
      <Card style={styles.card}>
        <Card.Content>
          <Paragraph style={styles.muted}>
            {"Scan the vendor's rotating pickup QR (or paste payload for testing). Pickup cannot complete without a valid scan."}
          </Paragraph>
          <TextInput
            label="Job ID"
            value={qrJobId}
            onChangeText={setQrJobId}
            mode="outlined"
            style={styles.input}
          />
          <TextInput
            label="QR payload (base64)"
            value={qrPayload}
            onChangeText={setQrPayload}
            mode="outlined"
            multiline
            style={styles.inputTall}
          />
          <Button mode="contained" onPress={submitQr} loading={busy} style={styles.btnGold}>
            Verify pickup
          </Button>
        </Card.Content>
      </Card>

      <Button mode="text" onPress={() => navigation.goBack()} textColor={luxuryColors.champagneGold}>
        Back
      </Button>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: luxuryColors.ivory },
  content: { padding: 16, paddingBottom: 32 },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: luxuryColors.ivory },
  heroKicker: {
    color: luxuryColors.champagneGold,
    letterSpacing: 2,
    fontSize: 11,
    textTransform: 'uppercase',
    marginBottom: 4,
  },
  heroTitle: {
    ...luxuryTypography.display,
    color: luxuryColors.matteBlack,
    fontSize: 26,
  },
  heroSub: {
    ...luxuryTypography.body,
    color: '#57534E',
    marginTop: 8,
    marginBottom: 16,
  },
  section: {
    ...luxuryTypography.display,
    color: luxuryColors.matteBlack,
    fontSize: 18,
    marginTop: 8,
    marginBottom: 8,
  },
  card: {
    marginBottom: 12,
    backgroundColor: '#fff',
    borderRadius: 16,
    borderWidth: 1,
    borderColor: luxuryColors.ivoryMuted,
  },
  rowBetween: { flexDirection: 'row', justifyContent: 'space-between' },
  label: { color: '#78716C', fontSize: 12, marginBottom: 4 },
  statusChip: { backgroundColor: luxuryColors.matteBlack, alignSelf: 'flex-start' },
  statusChipText: { color: luxuryColors.champagneGold },
  wallet: { ...luxuryTypography.display, fontSize: 24, color: luxuryColors.matteBlack },
  muted: { color: '#78716C', marginTop: 6 },
  jobId: { fontSize: 11, color: '#A8A29E' },
  jobLine: { ...luxuryTypography.body, fontSize: 16, color: luxuryColors.matteBlack, marginTop: 4 },
  actions: { flexDirection: 'row', gap: 8, marginTop: 12, flexWrap: 'wrap' },
  btnGold: { backgroundColor: luxuryColors.champagneGold },
  input: { marginTop: 8, backgroundColor: '#fff' },
  inputTall: { marginTop: 8, minHeight: 100, backgroundColor: '#fff' },
});

export default DeliveryPartnerDashboardScreen;
